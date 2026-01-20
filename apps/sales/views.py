from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from apps.sales.models import Order, Service
from apps.customers.models import Customer
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users

User = get_user_model()

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'CONSULTANT', 'TELESALE'])
def revenue_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    doctor_id = request.GET.get('doctor_id')
    consultant_id = request.GET.get('consultant_id')

    # Lọc đơn hàng
    orders = Order.objects.filter(
        order_date__range=[date_start, date_end]
    ).select_related('customer__assigned_telesale')

    if doctor_id: orders = orders.filter(appointment__assigned_doctor_id=doctor_id)
    if consultant_id: orders = orders.filter(assigned_consultant_id=consultant_id)

    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_revenue = orders.aggregate(Sum('actual_revenue'))['actual_revenue__sum'] or 0
    total_debt = orders.aggregate(Sum('debt_amount'))['debt_amount__sum'] or 0

    total_orders = orders.count()
    avg_order_value = round(total_sales / total_orders) if total_orders > 0 else 0

    # Dữ liệu biểu đồ doanh thu
    revenue_data = {}
    raw_orders = orders.values('order_date').annotate(daily_revenue=Sum('actual_revenue')).order_by('order_date')
    
    for item in raw_orders:
        d = item['order_date']
        if d:
            revenue_data[d] = float(item['daily_revenue'] or 0)
    
    sorted_dates = sorted(revenue_data.keys())
    chart_dates = [d.strftime('%d/%m') for d in sorted_dates]
    chart_revenues = [revenue_data[d] for d in sorted_dates]
    
    revenue_table = [{'date': d, 'amount': revenue_data[d]} for d in sorted_dates]

    # --- THỐNG KÊ CHI TIẾT HIỆU SUẤT SALE TƯ VẤN ---
    consultants_list = User.objects.filter(role='CONSULTANT')
    if consultant_id:
        consultants_list = consultants_list.filter(id=consultant_id)
        
    sale_performance_data = []

    for cons in consultants_list:
        apps = Appointment.objects.filter(
            assigned_consultant=cons, 
            appointment_date__date__range=[date_start, date_end]
        )
        
        assigned_count = apps.count()
        # Khách đã tiếp = Check-in (bao gồm thành công + thất bại)
        checkin_count = apps.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        
        success_count = apps.filter(status='COMPLETED', order__isnull=False).distinct().count()
        failed_count = apps.filter(status='COMPLETED', order__isnull=True).count()
        
        revenue_val = orders.filter(assigned_consultant=cons).aggregate(Sum('actual_revenue'))['actual_revenue__sum'] or 0
        
        # [MỚI] Tính trung bình doanh thu / khách đã tiếp
        avg_revenue = 0
        if checkin_count > 0:
            avg_revenue = revenue_val / checkin_count

        display_name = f"{cons.last_name} {cons.first_name}".strip() or cons.username

        sale_performance_data.append({
            'name': display_name,
            'assigned': assigned_count,
            'checkin': checkin_count,
            'success': success_count,
            'failed': failed_count,
            'revenue': revenue_val,
            'avg_revenue': avg_revenue # <--- Thêm trường này
        })
    
    sale_performance_data.sort(key=lambda x: x['revenue'], reverse=True)
    
    # ... (Các phần thống kê Telesale, Marketing giữ nguyên) ...
    revenue_by_telesale = orders.values(
        'customer__assigned_telesale__username',
        'customer__assigned_telesale__first_name',
        'customer__assigned_telesale__last_name'
    ).annotate(total=Sum('actual_revenue')).order_by('-total')

    telesale_revenue_table = []
    for item in revenue_by_telesale:
        username = item['customer__assigned_telesale__username']
        first = item['customer__assigned_telesale__first_name']
        last = item['customer__assigned_telesale__last_name']

        if not username:
            display_name = 'Không có Telesale'
        elif first or last:
            display_name = f"{last or ''} {first or ''}".strip()
        else:
            display_name = username
        
        telesale_revenue_table.append({'name': display_name, 'amount': float(item['total'] or 0)})

    new_customers = Customer.objects.filter(created_at__date__range=[date_start, date_end])
    marketing_total_leads = new_customers.count()

    source_stats = new_customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_dict = dict(Customer.Source.choices)
    mkt_source_labels = [source_dict.get(item['source'], item['source']) for item in source_stats]
    mkt_source_data = [item['count'] for item in source_stats]
    source_table = [{'name': source_dict.get(item['source'], item['source']), 'count': item['count']} for item in source_stats]

    skin_stats = new_customers.values('skin_condition').annotate(count=Count('id')).order_by('-count')
    skin_dict = dict(Customer.SkinIssue.choices)
    mkt_skin_labels = [skin_dict.get(item['skin_condition'], item['skin_condition']) for item in skin_stats]
    mkt_skin_data = [item['count'] for item in skin_stats]
    skin_table = [{'name': skin_dict.get(item['skin_condition'], item['skin_condition']), 'count': item['count']} for item in skin_stats]

    city_stats = new_customers.values('city').annotate(count=Count('id')).order_by('-count')[:10]
    mkt_city_labels = [item['city'] or 'Chưa rõ' for item in city_stats]
    mkt_city_data = [item['count'] for item in city_stats]
    city_table = [{'name': item['city'] or 'Chưa rõ', 'count': item['count']} for item in city_stats]

    age_groups = {'<18': 0, '18-25': 0, '26-35': 0, '36-45': 0, '46+': 0, 'Chưa rõ': 0}
    for cus in new_customers:
        age = cus.age
        if age is None: age_groups['Chưa rõ'] += 1
        elif age < 18: age_groups['<18'] += 1
        elif 18 <= age <= 25: age_groups['18-25'] += 1
        elif 26 <= age <= 35: age_groups['26-35'] += 1
        elif 36 <= age <= 45: age_groups['36-45'] += 1
        else: age_groups['46+'] += 1
    
    mkt_age_labels = list(age_groups.keys())
    mkt_age_data = list(age_groups.values())
    age_table = [{'group': k, 'count': v} for k, v in age_groups.items() if v > 0]

    logs = CallLog.objects.filter(call_time__date__range=[date_start, date_end])
    if consultant_id: logs = logs.filter(caller_id=consultant_id)

    total_calls = logs.count()
    status_stats = logs.values('status').annotate(count=Count('id')).order_by('-count')
    status_dict = dict(CallLog.CallStatus.choices)
    
    tele_status_labels = [status_dict.get(item['status'], item['status']) for item in status_stats]
    tele_status_data = [item['count'] for item in status_stats]
    tele_table = [{'status': status_dict.get(item['status'], item['status']), 'count': item['count']} for item in status_stats]

    doctors = User.objects.filter(role='DOCTOR')
    consultants = User.objects.filter(role='CONSULTANT')

    context = {
        'orders': orders.order_by('-order_date'),
        'total_revenue': total_revenue, 
        'total_sales': total_sales,
        'total_debt': total_debt,
        'total_orders': total_orders, 
        'avg_order_value': avg_order_value,
        'chart_dates': chart_dates, 
        'chart_revenues': chart_revenues,
        'sale_performance_data': sale_performance_data,
        'marketing_total_leads': marketing_total_leads,
        'mkt_source_labels': mkt_source_labels, 'mkt_source_data': mkt_source_data,
        'mkt_skin_labels': mkt_skin_labels, 'mkt_skin_data': mkt_skin_data,
        'mkt_city_labels': mkt_city_labels, 'mkt_city_data': mkt_city_data,
        'mkt_age_labels': mkt_age_labels, 'mkt_age_data': mkt_age_data,
        'total_calls': total_calls,
        'tele_status_labels': tele_status_labels, 'tele_status_data': tele_status_data,
        'revenue_table': revenue_table, 
        'telesale_revenue_table': telesale_revenue_table,
        'source_table': source_table, 'skin_table': skin_table,
        'city_table': city_table, 'age_table': age_table,
        'tele_table': tele_table,
        'date_start': date_start, 'date_end': date_end,
        'selected_doctor': int(doctor_id) if doctor_id else None,
        'selected_consultant': int(consultant_id) if consultant_id else None,
        'doctors': doctors, 'consultants': consultants,
    }
    return render(request, 'sales/revenue_dashboard.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN', 'TELESALE'])
def print_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
        'now': timezone.now(),
        'clinic_info': {
            'name': 'PHÒNG KHÁM THẨM MỸ V-MEDICAL',
            'address': '57A Trần Quốc Thảo, P.Võ Thị Sáu, Q.3, TP.HCM',
            'hotline': '0943 847 799',
            'website': 'https://vmedicalclinic.vn/'
        }
    }
    return render(request, 'sales/invoice_print.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def admin_dashboard(request):
    today = timezone.now().date()
    
    default_start = today.replace(day=1)
    default_end = today
    
    date_start_str = request.GET.get('date_start')
    date_end_str = request.GET.get('date_end')
    
    if date_start_str and date_end_str:
        try:
            date_start = datetime.strptime(date_start_str, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end_str, '%Y-%m-%d').date()
        except ValueError:
            date_start = default_start
            date_end = default_end
    else:
        date_start = default_start
        date_end = default_end

    delta = date_end - date_start
    days_diff = delta.days + 1
    previous_end = date_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days_diff - 1)

    revenue_current = Order.objects.filter(
        order_date__range=[date_start, date_end], is_paid=True
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    revenue_previous = Order.objects.filter(
        order_date__range=[previous_start, previous_end], is_paid=True
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    growth_rate = 0
    if revenue_previous > 0:
        growth_rate = ((revenue_current - revenue_previous) / revenue_previous) * 100
    elif revenue_current > 0:
        growth_rate = 100

    appts_total = Appointment.objects.filter(
        appointment_date__date__range=[date_start, date_end]
    ).values('customer').distinct().count()

    appts_arrived = Appointment.objects.filter(
        appointment_date__date__range=[date_start, date_end], 
        status__in=['ARRIVED', 'COMPLETED']
    ).values('customer').distinct().count()

    arrival_rate = (appts_arrived / appts_total * 100) if appts_total > 0 else 0

    calls_total = CallLog.objects.filter(call_time__date__range=[date_start, date_end]).count()
    leads_total = Customer.objects.filter(created_at__date__range=[date_start, date_end]).count()

    trend_orders = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True).values('order_date', 'total_amount')
    
    trend_data = {}
    for item in trend_orders:
        d = item['order_date']
        if d:
            trend_data[d] = trend_data.get(d, 0) + (item['total_amount'] or 0)
            
    sorted_trend = sorted(trend_data.keys())
    chart_labels = [d.strftime('%d/%m') for d in sorted_trend]
    chart_data = [float(trend_data[d]) for d in sorted_trend]

    top_services = Order.objects.filter(
        order_date__range=[date_start, date_end], 
        is_paid=True
    ).values('service__name').annotate(total=Sum('total_amount')).order_by('-total')[:5]
    
    service_labels = [item['service__name'] for item in top_services]
    service_data = [float(item['total']) for item in top_services]

    # --- [CẬP NHẬT] THỐNG KÊ CHI TIẾT SALE CÓ THÊM AVG_REVENUE ---
    consultants = User.objects.filter(role='CONSULTANT')
    consultant_stats_filtered = []
    
    for cons in consultants:
        apps_filtered = Appointment.objects.filter(
            assigned_consultant=cons, 
            appointment_date__date__range=[date_start, date_end]
        )
        
        assigned = apps_filtered.count()
        checkin = apps_filtered.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        success = apps_filtered.filter(status='COMPLETED', order__isnull=False).distinct().count()
        failed = apps_filtered.filter(status='COMPLETED', order__isnull=True).count()
        
        rev_filtered = Order.objects.filter(
            assigned_consultant=cons, 
            order_date__range=[date_start, date_end], 
            is_paid=True
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # [MỚI] Tính TB/Khách
        avg_revenue = 0
        if checkin > 0:
            avg_revenue = rev_filtered / checkin

        consultant_stats_filtered.append({
            'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
            'assigned': assigned,
            'checkin': checkin,
            'success': success,
            'failed': failed,
            'revenue': rev_filtered,
            'avg_revenue': avg_revenue # <--- Thêm trường này
        })
    # ---------------------------------------------------------------------------------

    top_telesales = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True)\
        .values('customer__assigned_telesale__username', 'customer__assigned_telesale__first_name', 'customer__assigned_telesale__last_name')\
        .annotate(total=Sum('total_amount')).order_by('-total')[:5]

    recent_orders = Order.objects.filter(order_date__range=[date_start, date_end]).order_by('-order_date')[:10]

    context = {
        'date_start': date_start.strftime('%Y-%m-%d'),
        'date_end': date_end.strftime('%Y-%m-%d'),
        'revenue_current': revenue_current,
        'growth_rate': growth_rate,
        'appts_total': appts_total,
        'appts_arrived': appts_arrived,
        'arrival_rate': arrival_rate,
        'calls_total': calls_total,
        'leads_total': leads_total,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'service_labels': service_labels,
        'service_data': service_data,
        'consultant_stats_filtered': consultant_stats_filtered,
        'top_telesales': top_telesales,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE'])
def debt_manager(request):
    orders = Order.objects.filter(debt_amount__gt=0).select_related('customer', 'service', 'assigned_consultant').order_by('-order_date')
    
    today = timezone.now().date()
    
    date_start = request.GET.get('date_start', '')
    date_end = request.GET.get('date_end', '')
    
    if date_start and date_end:
        try:
            d_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            d_end = datetime.strptime(date_end, '%Y-%m-%d').date()
            orders = orders.filter(order_date__range=[d_start, d_end])
        except ValueError:
            pass

    search_query = request.GET.get('q', '').strip()
    if search_query:
        orders = orders.filter(
            Q(customer__name__icontains=search_query) |
            Q(customer__phone__icontains=search_query) |
            Q(customer__customer_code__icontains=search_query)
        )

    total_debt = orders.aggregate(Sum('debt_amount'))['debt_amount__sum'] or 0
    total_count = orders.count()
    
    debt_by_sale = orders.values(
        'assigned_consultant__username', 
        'assigned_consultant__last_name', 
        'assigned_consultant__first_name'
    ).annotate(total=Sum('debt_amount')).order_by('-total')[:5]
    
    sale_labels = []
    sale_data = []
    
    for item in debt_by_sale:
        last = item['assigned_consultant__last_name']
        first = item['assigned_consultant__first_name']
        if last and first:
            name = f"{last} {first}"
        else:
            name = item['assigned_consultant__username'] or "Chưa gán"
        sale_labels.append(name)
        sale_data.append(float(item['total']))

    debt_by_date = orders.values('order_date').annotate(total=Sum('debt_amount')).order_by('order_date')
    date_labels = [item['order_date'].strftime('%d/%m') for item in debt_by_date]
    date_data = [float(item['total']) for item in debt_by_date]

    context = {
        'debt_orders': orders,
        'total_debt': total_debt,
        'total_count': total_count,
        'search_query': search_query,
        'date_start': date_start,
        'date_end': date_end,
        'sale_labels': sale_labels,
        'sale_data': sale_data,
        'date_labels': date_labels,
        'date_data': date_data,
    }
    return render(request, 'sales/debt_list.html', context)