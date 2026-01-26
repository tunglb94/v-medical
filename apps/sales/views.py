from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, CharField
from django.db.models.functions import Cast
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from apps.sales.models import Order, Service
from apps.customers.models import Customer
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- HÀM AN TOÀN TUYỆT ĐỐI ---
def safe_float(value):
    """Chuyển đổi bất cứ thứ gì thành số float, chấp nhận cả '1,000,000'"""
    if value is None: return 0.0
    try:
        # Nếu là số thì trả về luôn
        if isinstance(value, (int, float)):
            return float(value)
        # Nếu là chuỗi
        clean_val = str(value).replace(',', '').strip()
        if not clean_val: return 0.0
        return float(clean_val)
    except:
        return 0.0

# --- KỸ THUẬT CAST: BIẾN SỐ THÀNH CHỮ ĐỂ TRÁNH CRASH DB ---
def get_safe_orders(queryset):
    """
    Ép kiểu các cột Decimal sang CharField (Text) ngay trong câu truy vấn.
    Điều này đánh lừa Django để nó không cố convert dữ liệu rác thành số.
    """
    return queryset.annotate(
        txt_total=Cast('total_amount', CharField()),
        txt_revenue=Cast('actual_revenue', CharField()),
        txt_debt=Cast('debt_amount', CharField())
    ).defer('total_amount', 'actual_revenue', 'debt_amount')

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'CONSULTANT', 'TELESALE'])
def revenue_dashboard(request):
    # Khai báo biến sớm để tránh NameError
    doctors = User.objects.filter(role='DOCTOR')
    consultants = User.objects.filter(role='CONSULTANT')
    services = Service.objects.all().order_by('name')
    telesales_list = User.objects.filter(role='TELESALE').order_by('first_name')

    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    doctor_id = request.GET.get('doctor_id')
    consultant_id = request.GET.get('consultant_id')

    # 1. Query Orders Cơ bản
    orders_qs = Order.objects.filter(
        order_date__range=[date_start, date_end]
    ).select_related('customer__assigned_telesale', 'service', 'assigned_consultant')

    if doctor_id: 
        orders_qs = orders_qs.filter(appointment__assigned_doctor_id=doctor_id)
    if consultant_id: 
        if consultant_id == 'none':
            orders_qs = orders_qs.filter(assigned_consultant__isnull=True)
        elif consultant_id.isdigit():
            orders_qs = orders_qs.filter(assigned_consultant_id=consultant_id)

    # 2. Áp dụng Safe Mode (Lấy dữ liệu dạng Text)
    # Lưu ý: Convert sang list ngay để ngắt kết nối DB
    orders = list(get_safe_orders(orders_qs))

    # 3. Tính toán bằng Python Loop (Không dùng Aggregate)
    total_sales = 0
    total_revenue = 0
    total_debt = 0
    total_orders_success = 0
    
    for o in orders:
        # Lấy từ field txt_... đã ép kiểu
        t_amt = safe_float(o.txt_total)
        rev = safe_float(o.txt_revenue)
        debt = safe_float(o.txt_debt)
        
        # Gán ngược lại vào object để dùng ở template (nếu cần)
        o.safe_total = t_amt 
        o.safe_revenue = rev
        
        total_sales += t_amt
        total_revenue += rev
        total_debt += debt
        
        if t_amt > 0:
            total_orders_success += 1
    
    avg_order_value = int(total_sales / total_orders_success) if total_orders_success > 0 else 0

    # 4. Lấy Ca thất bại
    failed_apps = Appointment.objects.filter(
        appointment_date__date__range=[date_start, date_end],
        status='COMPLETED',
        order__isnull=True
    ).select_related('customer', 'assigned_consultant', 'customer__assigned_telesale')

    if doctor_id: failed_apps = failed_apps.filter(assigned_doctor_id=doctor_id)
    if consultant_id:
        if consultant_id == 'none': failed_apps = failed_apps.filter(assigned_consultant__isnull=True)
        elif consultant_id.isdigit(): failed_apps = failed_apps.filter(assigned_consultant_id=consultant_id)

    # 5. Gộp Log
    order_logs = []
    for o in orders:
        amt = safe_float(o.txt_total)
        order_logs.append({
            'is_fail': (amt == 0),
            'id': o.id, 'item_id': o.id, 'type': 'order', 'date': o.order_date,
            'customer_name': o.customer.name, 'customer_phone': o.customer.phone,
            'service_name': o.service.name if o.service else "Khác",
            'service_id': o.service.id if o.service else "",
            'consultant': o.assigned_consultant, 'telesale': o.customer.assigned_telesale,
            'total_amount': amt
        })
        
    for app in failed_apps:
        order_logs.append({
            'is_fail': True, 'id': app.id, 'item_id': app.id, 'type': 'appointment', 
            'date': app.appointment_date.date(),
            'customer_name': app.customer.name, 'customer_phone': app.customer.phone,
            'service_name': "Không phát sinh dịch vụ (Fail)", 'service_id': "",
            'consultant': app.assigned_consultant, 'telesale': app.customer.assigned_telesale,
            'total_amount': 0
        })
    order_logs.sort(key=lambda x: x['date'], reverse=True)

    # 6. Biểu đồ & Bảng
    revenue_data = {}
    for o in orders:
        d = o.order_date
        if d: revenue_data[d] = revenue_data.get(d, 0) + safe_float(o.txt_revenue)
    
    sorted_dates = sorted(revenue_data.keys())
    chart_dates = [d.strftime('%d/%m') for d in sorted_dates]
    chart_revenues = [revenue_data[d] for d in sorted_dates]
    revenue_table = [{'date': d, 'amount': revenue_data[d]} for d in sorted_dates]

    # 7. Hiệu suất Sale
    consultants_list_filter = consultants
    if consultant_id and consultant_id.isdigit():
        consultants_list_filter = consultants_list_filter.filter(id=consultant_id)
        
    sale_performance_data = []
    for cons in consultants_list_filter:
        apps = Appointment.objects.filter(assigned_consultant=cons, appointment_date__date__range=[date_start, date_end])
        assigned_count = apps.count()
        checkin_count = apps.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        
        my_orders = [o for o in orders if o.assigned_consultant_id == cons.id]
        
        success_count = apps.filter(status='COMPLETED', order__total_amount__gt=0).count()
        completed_total = apps.filter(status='COMPLETED').count()
        failed_count = max(0, completed_total - success_count)
        
        rev_val = sum(safe_float(o.txt_revenue) for o in my_orders)
        real_orders = sum(1 for o in my_orders if safe_float(o.txt_total) > 0)
        
        if assigned_count > 0 or len(my_orders) > 0:
            sale_performance_data.append({
                'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
                'assigned': assigned_count, 'checkin': checkin_count,
                'success': success_count, 'failed': failed_count,
                'total_orders': real_orders, 'revenue': rev_val,
                'avg_revenue': int(rev_val / checkin_count) if checkin_count > 0 else 0
            })
    sale_performance_data.sort(key=lambda x: x['revenue'], reverse=True)

    # 8. Telesale
    telesale_map = {}
    for o in orders:
        tele = o.customer.assigned_telesale
        rev = safe_float(o.txt_revenue)
        name = f"{tele.last_name} {tele.first_name}".strip() if (tele and tele.first_name) else (tele.username if tele else "Không có Telesale")
        telesale_map[name] = telesale_map.get(name, 0) + rev
    
    telesale_revenue_table = [{'name': k, 'amount': v} for k, v in sorted(telesale_map.items(), key=lambda x: x[1], reverse=True)]

    context = {
        'orders': orders, 'order_logs': order_logs,
        'total_revenue': total_revenue, 'total_sales': total_sales, 'total_debt': total_debt,
        'total_orders': total_orders_success, 'avg_order_value': avg_order_value,
        'chart_dates': chart_dates, 'chart_revenues': chart_revenues,
        'sale_performance_data': sale_performance_data, 'telesale_revenue_table': telesale_revenue_table,
        'revenue_table': revenue_table, 
        'date_start': date_start, 'date_end': date_end,
        'selected_doctor': int(doctor_id) if doctor_id else None,
        'selected_consultant': int(consultant_id) if consultant_id and consultant_id.isdigit() else consultant_id,
        'doctors': doctors, 
        'consultants': consultants,
        'services': services, 
        'telesales_list': telesales_list,
    }
    return render(request, 'sales/revenue_dashboard.html', context)

# --- GIỮ NGUYÊN UPDATE ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MANAGER', 'RECEPTIONIST', 'TELESALE'])
def update_order_details(request):
    if request.method == "POST":
        try:
            item_id = request.POST.get('item_id')
            item_type = request.POST.get('item_type')
            new_cons = User.objects.get(id=request.POST.get('consultant_id')) if request.POST.get('consultant_id') else None
            new_service = Service.objects.get(id=request.POST.get('service_id')) if request.POST.get('service_id') else None
            new_telesale = User.objects.get(id=request.POST.get('telesale_id')) if request.POST.get('telesale_id') else None
            new_amount = request.POST.get('total_amount')
            new_date = request.POST.get('order_date')

            target_customer = None
            if item_type == 'order':
                order = Order.objects.get(id=item_id)
                target_customer = order.customer
                order.assigned_consultant = new_cons
                if new_service: order.service = new_service
                
                if new_amount:
                    clean_amt = safe_float(new_amount)
                    order.total_amount = clean_amt
                    order.actual_revenue = clean_amt
                
                if new_date: order.order_date = new_date
                order.save()
                
                if order.appointment:
                    order.appointment.assigned_consultant = new_cons
                    order.appointment.save()
                messages.success(request, f"Đã cập nhật đơn hàng #{order.id}")
                
            elif item_type == 'appointment':
                appt = Appointment.objects.get(id=item_id)
                target_customer = appt.customer
                appt.assigned_consultant = new_cons
                if new_date:
                    original_time = appt.appointment_date.time()
                    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
                    appt.appointment_date = datetime.combine(new_date_obj, original_time)
                appt.save()
                messages.success(request, f"Đã cập nhật lịch hẹn")

            if target_customer and request.POST.get('telesale_id') is not None:
                target_customer.assigned_telesale = new_telesale
                target_customer.save()
        except Exception as e:
            messages.error(request, f"Lỗi cập nhật: {e}")
    return redirect(request.META.get('HTTP_REFERER', 'sales_report'))

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN', 'TELESALE'])
def print_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Fix hiển thị an toàn
    order.safe_total = safe_float(order.total_amount)
    return render(request, 'sales/invoice_print.html', {
        'order': order, 'now': timezone.now(),
        'clinic_info': {'name': 'PHÒNG KHÁM THẨM MỸ V-MEDICAL', 'address': '57A Trần Quốc Thảo...', 'hotline': '0943 847 799'}
    })

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE'])
def debt_manager(request):
    # Sử dụng get_safe_orders cho Debt luôn để tránh crash
    qs = Order.objects.select_related('customer', 'service', 'assigned_consultant').order_by('-order_date')
    orders_safe = get_safe_orders(qs)
    
    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')
    search_query = request.GET.get('q', '').strip().lower()
    
    d_start, d_end = None, None
    if date_start and date_end:
        try:
            d_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            d_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except: pass

    filtered_orders = []
    total_debt = 0
    
    for o in orders_safe:
        if d_start and d_end and not (d_start <= o.order_date <= d_end): continue
        if search_query:
            if (search_query not in (o.customer.name or '').lower()) and (search_query not in (o.customer.phone or '').lower()):
                continue
        
        debt = safe_float(o.txt_debt)
        if debt > 0:
            o.safe_debt = debt
            filtered_orders.append(o)
            total_debt += debt

    debt_by_sale = {}
    debt_by_date = {}
    for o in filtered_orders:
        cons = o.assigned_consultant
        name = f"{cons.last_name} {cons.first_name}".strip() if (cons and cons.first_name) else (cons.username if cons else "Chưa gán")
        debt_by_sale[name] = debt_by_sale.get(name, 0) + o.safe_debt
        debt_by_date[o.order_date] = debt_by_date.get(o.order_date, 0) + o.safe_debt

    sorted_sale = sorted(debt_by_sale.items(), key=lambda x: x[1], reverse=True)[:5]
    sorted_dates = sorted(debt_by_date.keys())

    context = {
        'debt_orders': filtered_orders, 'total_debt': total_debt, 'total_count': len(filtered_orders),
        'search_query': search_query, 'date_start': date_start, 'date_end': date_end,
        'sale_labels': [k for k,v in sorted_sale], 'sale_data': [v for k,v in sorted_sale],
        'date_labels': [d.strftime('%d/%m') for d in sorted_dates], 'date_data': [debt_by_date[d] for d in sorted_dates],
    }
    return render(request, 'sales/debt_list.html', context)

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
        except:
            date_start, date_end = default_start, default_end
    else:
        date_start, date_end = default_start, default_end

    delta = date_end - date_start
    days_diff = delta.days + 1
    prev_end = date_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days_diff)

    # --- SỬ DỤNG HÀM get_safe_orders ĐỂ TRÁNH CRASH ---
    qs_current = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True)
    orders_current = list(get_safe_orders(qs_current))
    
    qs_prev = Order.objects.filter(order_date__range=[prev_start, prev_end], is_paid=True)
    orders_prev = list(get_safe_orders(qs_prev))

    revenue_current = 0
    trend_data = {}
    service_map = {}
    telesale_map = {}

    for o in orders_current:
        # Lấy từ txt_total thay vì total_amount
        amt = safe_float(o.txt_total)
        revenue_current += amt
        
        if o.order_date: trend_data[o.order_date] = trend_data.get(o.order_date, 0) + amt
        
        svc = o.service
        svc_name = svc.name if svc else "Khác"
        service_map[svc_name] = service_map.get(svc_name, 0) + amt
        
        tele = o.customer.assigned_telesale if o.customer else None
        tele_name = f"{tele.last_name} {tele.first_name}".strip() if (tele and tele.first_name) else (tele.username if tele else "Không có Telesale")
        telesale_map[tele_name] = telesale_map.get(tele_name, 0) + amt

    revenue_previous = 0
    for o in orders_prev:
        revenue_previous += safe_float(o.txt_total)

    growth_rate = 0
    if revenue_previous > 0:
        growth_rate = ((revenue_current - revenue_previous) / revenue_previous) * 100
    elif revenue_current > 0: growth_rate = 100

    appts_total = Appointment.objects.filter(appointment_date__date__range=[date_start, date_end]).values('customer').distinct().count()
    appts_arrived = Appointment.objects.filter(appointment_date__date__range=[date_start, date_end], status__in=['ARRIVED', 'COMPLETED']).values('customer').distinct().count()
    arrival_rate = (appts_arrived / appts_total * 100) if appts_total > 0 else 0
    
    calls_total = CallLog.objects.filter(call_time__date__range=[date_start, date_end]).count()
    leads_total = Customer.objects.filter(created_at__date__range=[date_start, date_end]).count()

    sorted_trend = sorted(trend_data.keys())
    chart_labels = [d.strftime('%d/%m') for d in sorted_trend]
    chart_data = [trend_data[d] for d in sorted_trend]

    sorted_svc = sorted(service_map.items(), key=lambda x: x[1], reverse=True)[:5]
    service_labels = [k for k,v in sorted_svc]
    service_data = [v for k,v in sorted_svc]

    sorted_tele = sorted(telesale_map.items(), key=lambda x: x[1], reverse=True)[:5]
    top_telesales = [{'name': k, 'total': v} for k,v in sorted_tele]

    consultants = User.objects.filter(role='CONSULTANT')
    consultant_stats_filtered = []
    
    for cons in consultants:
        apps_filtered = Appointment.objects.filter(assigned_consultant=cons, appointment_date__date__range=[date_start, date_end])
        assigned = apps_filtered.count()
        checkin = apps_filtered.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        success = apps_filtered.filter(status='COMPLETED', order__isnull=False).distinct().count()
        failed = apps_filtered.filter(status='COMPLETED', order__isnull=True).count()
        
        my_orders = [o for o in orders_current if o.assigned_consultant_id == cons.id]
        rev_filtered = sum(safe_float(o.txt_total) for o in my_orders)
        
        if assigned > 0 or len(my_orders) > 0:
            consultant_stats_filtered.append({
                'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
                'assigned': assigned, 'checkin': checkin, 'success': success,
                'failed': failed, 'total_orders': len(my_orders), 'revenue': rev_filtered,
                'avg_revenue': int(rev_filtered / checkin) if checkin > 0 else 0
            })

    # [FIX CRITICAL] Dùng get_safe_orders cho cả Recent Orders
    qs_recent = Order.objects.filter(order_date__range=[date_start, date_end]).order_by('-order_date')[:10]
    recent_orders = []
    # Loop và gán giá trị safe để hiển thị
    for o in list(get_safe_orders(qs_recent)):
        o.safe_total = safe_float(o.txt_total)
        recent_orders.append(o)

    context = {
        'date_start': date_start.strftime('%Y-%m-%d'),
        'date_end': date_end.strftime('%Y-%m-%d'),
        'revenue_current': revenue_current, 'revenue_previous': revenue_previous, 'growth_rate': growth_rate,
        'appts_total': appts_total, 'appts_arrived': appts_arrived, 'arrival_rate': arrival_rate,
        'calls_total': calls_total, 'leads_total': leads_total,
        'chart_labels': chart_labels, 'chart_data': chart_data,
        'service_labels': service_labels, 'service_data': service_data,
        'consultant_stats_filtered': consultant_stats_filtered,
        'top_telesales': top_telesales,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_dashboard.html', context)