from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

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
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    doctor_id = request.GET.get('doctor_id')
    consultant_id = request.GET.get('consultant_id')

    orders = Order.objects.filter(
        created_at__date__range=[date_start, date_end],
        is_paid=True
    )

    if doctor_id: orders = orders.filter(appointment__assigned_doctor_id=doctor_id)
    if consultant_id: orders = orders.filter(sale_consultant_id=consultant_id)

    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = orders.count()
    avg_order_value = round(total_revenue / total_orders) if total_orders > 0 else 0

    # Chart Data: Doanh thu theo ngày
    revenue_by_date = orders.annotate(date=TruncDate('created_at')).values('date').annotate(daily_revenue=Sum('total_amount')).order_by('date')
    chart_dates = [item['date'].strftime('%d/%m') for item in revenue_by_date]
    chart_revenues = [float(item['daily_revenue']) for item in revenue_by_date]
    revenue_table = [{'date': item['date'], 'amount': item['daily_revenue']} for item in revenue_by_date]

    # Chart Data: Doanh thu theo Sale
    revenue_by_sale = orders.values('sale_consultant__username').annotate(total=Sum('total_amount')).order_by('-total')
    sale_labels = [item['sale_consultant__username'] or 'Chưa gán' for item in revenue_by_sale]
    sale_data = [float(item['total']) for item in revenue_by_sale]
    sale_table = [{'name': item['sale_consultant__username'] or 'Chưa gán', 'amount': item['total']} for item in revenue_by_sale]

    # Marketing Data (Khách hàng mới)
    new_customers = Customer.objects.filter(created_at__date__range=[date_start, date_end])
    marketing_total_leads = new_customers.count()

    # Nguồn khách
    source_stats = new_customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_dict = dict(Customer.Source.choices)
    mkt_source_labels = [source_dict.get(item['source'], item['source']) for item in source_stats]
    mkt_source_data = [item['count'] for item in source_stats]
    source_table = [{'name': source_dict.get(item['source'], item['source']), 'count': item['count']} for item in source_stats]

    # Vấn đề da
    skin_stats = new_customers.values('skin_condition').annotate(count=Count('id')).order_by('-count')
    skin_dict = dict(Customer.SkinIssue.choices)
    mkt_skin_labels = [skin_dict.get(item['skin_condition'], item['skin_condition']) for item in skin_stats]
    mkt_skin_data = [item['count'] for item in skin_stats]
    skin_table = [{'name': skin_dict.get(item['skin_condition'], item['skin_condition']), 'count': item['count']} for item in skin_stats]

    # Tỉnh thành
    city_stats = new_customers.values('city').annotate(count=Count('id')).order_by('-count')[:10]
    mkt_city_labels = [item['city'] or 'Chưa rõ' for item in city_stats]
    mkt_city_data = [item['count'] for item in city_stats]
    city_table = [{'name': item['city'] or 'Chưa rõ', 'count': item['count']} for item in city_stats]

    # Độ tuổi (Sử dụng property 'age' từ model Customer)
    age_groups = {'<18': 0, '18-25': 0, '26-35': 0, '36-45': 0, '46+': 0, 'Chưa rõ': 0}
    for cus in new_customers:
        age = cus.age # Lấy tuổi từ property tính theo DOB
        if age is None: age_groups['Chưa rõ'] += 1
        elif age < 18: age_groups['<18'] += 1
        elif 18 <= age <= 25: age_groups['18-25'] += 1
        elif 26 <= age <= 35: age_groups['26-35'] += 1
        elif 36 <= age <= 45: age_groups['36-45'] += 1
        else: age_groups['46+'] += 1
    
    mkt_age_labels = list(age_groups.keys())
    mkt_age_data = list(age_groups.values())
    age_table = [{'group': k, 'count': v} for k, v in age_groups.items() if v > 0]

    # Telesale Data
    logs = CallLog.objects.filter(call_time__date__range=[date_start, date_end])
    if consultant_id: logs = logs.filter(caller_id=consultant_id)

    total_calls = logs.count()
    status_stats = logs.values('status').annotate(count=Count('id')).order_by('-count')
    status_dict = dict(CallLog.CallStatus.choices)
    
    tele_status_labels = [status_dict.get(item['status'], item['status']) for item in status_stats]
    tele_status_data = [item['count'] for item in status_stats]
    tele_table = [{'status': status_dict.get(item['status'], item['status']), 'count': item['count']} for item in status_stats]

    # Danh sách nhân sự để lọc
    doctors = User.objects.filter(role='DOCTOR')
    consultants = User.objects.filter(role='CONSULTANT')

    context = {
        'orders': orders.order_by('-created_at'),
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


# --- 2. IN HÓA ĐƠN (LỄ TÂN + ADMIN) ---
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


# --- 3. DASHBOARD TỔNG QUAN CHO SẾP (PRO VERSION) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def admin_dashboard(request):
    today = timezone.now().date()
    this_month = today.month
    this_year = today.year
    
    # --- A. KPI TÀI CHÍNH & TĂNG TRƯỞNG ---
    # Doanh thu tháng này
    revenue_this_month = Order.objects.filter(
        created_at__month=this_month, 
        created_at__year=this_year, 
        is_paid=True
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Doanh thu tháng trước (để tính tăng trưởng)
    last_month_date = today.replace(day=1) - timedelta(days=1)
    revenue_last_month = Order.objects.filter(
        created_at__month=last_month_date.month, 
        created_at__year=last_month_date.year, 
        is_paid=True
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Tính % tăng trưởng
    growth_rate = 0
    if revenue_last_month > 0:
        growth_rate = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
    elif revenue_this_month > 0:
        growth_rate = 100 # Tăng trưởng tuyệt đối

    # --- B. KPI VẬN HÀNH HÔM NAY ---
    appts_today_total = Appointment.objects.filter(appointment_date__date=today).count()
    # Tỷ lệ đến: (Đã đến + Hoàn thành) / Tổng hẹn
    appts_arrived = Appointment.objects.filter(appointment_date__date=today, status__in=['ARRIVED', 'COMPLETED']).count()
    arrival_rate = (appts_arrived / appts_today_total * 100) if appts_today_total > 0 else 0

    new_leads_month = Customer.objects.filter(created_at__month=this_month, created_at__year=this_year).count()
    calls_today = CallLog.objects.filter(call_time__date=today).count()
    leads_today = Customer.objects.filter(created_at__date=today).count()
    revenue_today = Order.objects.filter(created_at__date=today, is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # --- C. BIỂU ĐỒ DOANH THU 30 NGÀY (TREND) ---
    last_30_days = today - timedelta(days=30)
    revenue_30d = Order.objects.filter(created_at__date__range=[last_30_days, today], is_paid=True)\
        .annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('total_amount')).order_by('date')
    
    chart_labels = [item['date'].strftime('%d/%m') for item in revenue_30d]
    chart_data = [float(item['total']) for item in revenue_30d]

    # --- D. TOP DỊCH VỤ BÁN CHẠY (PIE CHART) ---
    top_services = Order.objects.filter(is_paid=True).values('treatment_name')\
        .annotate(total=Sum('total_amount')).order_by('-total')[:5]
    
    service_labels = [item['treatment_name'] for item in top_services]
    service_data = [float(item['total']) for item in top_services]

    # --- E. TOP NHÂN VIÊN XUẤT SẮC THÁNG ---
    top_sales = Order.objects.filter(created_at__month=this_month, is_paid=True)\
        .values('sale_consultant__username', 'sale_consultant__first_name', 'sale_consultant__last_name')\
        .annotate(total=Sum('total_amount')).order_by('-total')[:5]

    # Giao dịch gần đây
    recent_orders = Order.objects.order_by('-created_at')[:6]
    recent_appts = Appointment.objects.order_by('-created_at')[:6]

    context = {
        # KPI Cards
        'revenue_today': revenue_today,
        'revenue_this_month': revenue_this_month,
        'growth_rate': growth_rate,
        'appts_today_total': appts_today_total,
        'appts_today_arrived': appts_today_arrived,
        'arrival_rate': arrival_rate,
        'new_leads_month': new_leads_month,
        'calls_today': calls_today,
        'leads_today': leads_today,
        
        # Charts
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'service_labels': service_labels,
        'service_data': service_data,
        
        # Lists
        'top_sales': top_sales,
        'recent_orders': recent_orders,
        'recent_appts': recent_appts,
    }
    return render(request, 'admin_dashboard.html', context)