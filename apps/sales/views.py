from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta # <--- Import thêm datetime

from apps.sales.models import Order, Service
from apps.customers.models import Customer
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- 1. BÁO CÁO DOANH THU (CHỈ ADMIN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def revenue_dashboard(request):
    # (Giữ nguyên code hàm revenue_dashboard như cũ)
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    doctor_id = request.GET.get('doctor_id')
    consultant_id = request.GET.get('consultant_id')

    orders = Order.objects.filter(
        # Đã sửa: created_at__date__range -> order_date__range
        order_date__range=[date_start, date_end],
        is_paid=True
    )

    if doctor_id: orders = orders.filter(appointment__assigned_doctor_id=doctor_id)
    # Đã sửa: sale_consultant_id -> assigned_consultant_id
    if consultant_id: orders = orders.filter(assigned_consultant_id=consultant_id)

    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = orders.count()
    avg_order_value = round(total_revenue / total_orders) if total_orders > 0 else 0

    # Đã sửa: TruncDate('created_at') -> TruncDate('order_date')
    revenue_by_date = orders.annotate(date=TruncDate('order_date')).values('date').annotate(daily_revenue=Sum('total_amount')).order_by('date')
    chart_dates = [item['date'].strftime('%d/%m') for item in revenue_by_date]
    chart_revenues = [float(item['daily_revenue']) for item in revenue_by_date]
    revenue_table = [{'date': item['date'], 'amount': item['daily_revenue']} for item in revenue_by_date]

    # Đã sửa: sale_consultant__username -> assigned_consultant__username
    revenue_by_sale = orders.values('assigned_consultant__username').annotate(total=Sum('total_amount')).order_by('-total')
    # Đã sửa: item['sale_consultant__username'] -> item['assigned_consultant__username']
    sale_labels = [item['assigned_consultant__username'] or 'Chưa gán' for item in revenue_by_sale]
    sale_data = [float(item['total']) for item in revenue_by_sale]
    # Đã sửa: item['sale_consultant__username'] -> item['assigned_consultant__username']
    sale_table = [{'name': item['assigned_consultant__username'] or 'Chưa gán', 'amount': item['total']} for item in revenue_by_sale]

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
        # Đã sửa: orders.order_by('-created_at') -> orders.order_by('-order_date')
        'orders': orders.order_by('-order_date'),
        'total_revenue': total_revenue, 'total_orders': total_orders, 'avg_order_value': avg_order_value,
        'chart_dates': chart_dates, 'chart_revenues': chart_revenues,
        'sale_labels': sale_labels, 'sale_data': sale_data,
        'marketing_total_leads': marketing_total_leads,
        'mkt_source_labels': mkt_source_labels, 'mkt_source_data': mkt_source_data,
        'mkt_skin_labels': mkt_skin_labels, 'mkt_skin_data': mkt_skin_data,
        'mkt_city_labels': mkt_city_labels, 'mkt_city_data': mkt_city_data,
        'mkt_age_labels': mkt_age_labels, 'mkt_age_data': mkt_age_data,
        'total_calls': total_calls,
        'tele_status_labels': tele_status_labels, 'tele_status_data': tele_status_data,
        'revenue_table': revenue_table, 'sale_table': sale_table,
        'source_table': source_table, 'skin_table': skin_table,
        'city_table': city_table, 'age_table': age_table,
        'tele_table': tele_table,
        'date_start': date_start, 'date_end': date_end,
        'selected_doctor': int(doctor_id) if doctor_id else None,
        'selected_consultant': int(consultant_id) if consultant_id else None,
        'doctors': doctors, 'consultants': consultants,
    }
    return render(request, 'sales/revenue_dashboard.html', context)


# --- 2. IN HÓA ĐƠN ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN'])
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


# --- 3. DASHBOARD TỔNG QUAN (ADMIN PRO - LỌC THEO NGÀY) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def admin_dashboard(request):
    today = timezone.now().date()
    
    # 1. Xử lý bộ lọc ngày
    # Mặc định: Tháng này (Từ ngày 1 đến hôm nay)
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

    # 2. Tính toán kỳ trước (Previous Period) để so sánh
    # Ví dụ: Chọn xem 7 ngày -> So sánh với 7 ngày trước đó
    delta = date_end - date_start
    days_diff = delta.days + 1
    previous_end = date_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days_diff - 1)

    # --- A. KPI TÀI CHÍNH (DOANH THU TRONG KỲ) ---
    revenue_current = Order.objects.filter(
        # Đã sửa: created_at -> order_date
        order_date__range=[date_start, date_end], is_paid=True
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    revenue_previous = Order.objects.filter(
        # Đã sửa: created_at -> order_date
        order_date__range=[previous_start, previous_end], is_paid=True
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    growth_rate = 0
    if revenue_previous > 0:
        growth_rate = ((revenue_current - revenue_previous) / revenue_previous) * 100
    elif revenue_current > 0:
        growth_rate = 100

    # --- B. KPI VẬN HÀNH TRONG KỲ ---
    # Tổng lịch hẹn
    appts_total = Appointment.objects.filter(appointment_date__date__range=[date_start, date_end]).count()
    
    # Khách đã đến (Arrived + Completed)
    appts_arrived = Appointment.objects.filter(
        appointment_date__date__range=[date_start, date_end], 
        status__in=['ARRIVED', 'COMPLETED']
    ).count()
    
    arrival_rate = (appts_arrived / appts_total * 100) if appts_total > 0 else 0

    # Telesale
    calls_total = CallLog.objects.filter(call_time__date__range=[date_start, date_end]).count()
    
    # Leads mới
    leads_total = Customer.objects.filter(created_at__date__range=[date_start, date_end]).count()

    # --- C. BIỂU ĐỒ (TREND) TRONG KỲ ---
    revenue_trend = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True)\
        .annotate(date=TruncDate('order_date')).values('date').annotate(total=Sum('total_amount')).order_by('date')
    
    chart_labels = [item['date'].strftime('%d/%m') for item in revenue_trend]
    chart_data = [float(item['total']) for item in revenue_trend]

    # --- D. TOP DỊCH VỤ ---
    top_services = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True)\
        # Sửa lỗi: treatment_name -> service__name
        .values('service__name').annotate(total=Sum('total_amount')).order_by('-total')[:5]
    
    # Sửa lỗi: item['treatment_name'] -> item['service__name']
    service_labels = [item['service__name'] for item in top_services]
    service_data = [float(item['total']) for item in top_services]

    # --- E. TOP NHÂN VIÊN ---
    top_sales = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True)\
        .values('assigned_consultant__username', 'assigned_consultant__first_name', 'assigned_consultant__last_name')\
        .annotate(total=Sum('total_amount')).order_by('-total')[:5]

    # Giao dịch gần đây (trong kỳ)
    recent_orders = Order.objects.filter(order_date__range=[date_start, date_end]).order_by('-order_date')[:10]

    context = {
        'date_start': date_start.strftime('%Y-%m-%d'),
        'date_end': date_end.strftime('%Y-%m-%d'),
        
        # KPI Cards
        'revenue_current': revenue_current,
        'growth_rate': growth_rate,
        'appts_total': appts_total,
        'appts_arrived': appts_arrived,
        'arrival_rate': arrival_rate,
        'calls_total': calls_total,
        'leads_total': leads_total,
        
        # Charts
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'service_labels': service_labels,
        'service_data': service_data,
        
        # Tables
        'top_sales': top_sales,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_dashboard.html', context)