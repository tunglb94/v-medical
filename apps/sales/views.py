from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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

# --- HÀM AN TOÀN: Chuyển đổi dữ liệu lỗi thành số 0 để không sập web ---
def safe_float(value):
    if value is None:
        return 0.0
    try:
        # Nếu là số thì trả về luôn
        if isinstance(value, (int, float)):
            return float(value)
        # Nếu là chuỗi thì xóa dấu phẩy và khoảng trắng
        clean_val = str(value).replace(',', '').strip()
        if clean_val == '':
            return 0.0
        return float(clean_val)
    except:
        return 0.0

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'CONSULTANT', 'TELESALE'])
def revenue_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    doctor_id = request.GET.get('doctor_id')
    consultant_id = request.GET.get('consultant_id')

    # --- 1. LẤY ĐƠN HÀNG (Order) ---
    orders = Order.objects.filter(
        order_date__range=[date_start, date_end]
    ).select_related('customer__assigned_telesale', 'service', 'assigned_consultant')

    if doctor_id: 
        orders = orders.filter(appointment__assigned_doctor_id=doctor_id)
    if consultant_id: 
        if consultant_id == 'none':
            orders = orders.filter(assigned_consultant__isnull=True)
        elif consultant_id.isdigit():
            orders = orders.filter(assigned_consultant_id=consultant_id)

    # --- TÍNH TOÁN AN TOÀN (Thay thế aggregate) ---
    # Chuyển QuerySet thành List để xử lý Python thuần (tránh lỗi Database)
    orders_list = list(orders)
    
    total_sales = 0
    total_revenue = 0
    total_debt = 0
    total_orders_success = 0
    
    for o in orders_list:
        t_amt = safe_float(o.total_amount)
        act_rev = safe_float(o.actual_revenue)
        debt = safe_float(o.debt_amount)
        
        total_sales += t_amt
        total_revenue += act_rev
        total_debt += debt
        
        if t_amt > 0:
            total_orders_success += 1
    
    avg_order_value = 0
    if total_orders_success > 0:
        avg_order_value = int(total_sales / total_orders_success)

    # --- 2. LẤY CA THẤT BẠI ---
    failed_apps = Appointment.objects.filter(
        appointment_date__date__range=[date_start, date_end],
        status='COMPLETED',
        order__isnull=True
    ).select_related('customer', 'assigned_consultant', 'customer__assigned_telesale')

    if doctor_id: 
        failed_apps = failed_apps.filter(assigned_doctor_id=doctor_id)
    if consultant_id:
        if consultant_id == 'none':
            failed_apps = failed_apps.filter(assigned_consultant__isnull=True)
        elif consultant_id.isdigit():
            failed_apps = failed_apps.filter(assigned_consultant_id=consultant_id)

    # --- 3. GỘP DANH SÁCH NHẬT KÝ ---
    order_logs = []
    
    # a. Thêm Order
    for o in orders_list:
        amt = safe_float(o.total_amount)
        is_zero_amount = (amt == 0)
        order_logs.append({
            'is_fail': is_zero_amount,
            'id': o.id,
            'item_id': o.id, 
            'type': 'order', 
            'date': o.order_date,
            'customer_name': o.customer.name,
            'customer_phone': o.customer.phone,
            'service_name': o.service.name if o.service else "Khác",
            'service_id': o.service.id if o.service else "",
            'consultant': o.assigned_consultant,
            'telesale': o.customer.assigned_telesale,
            'total_amount': amt
        })
        
    # b. Thêm Appointment
    for app in failed_apps:
        order_logs.append({
            'is_fail': True,
            'id': app.id, 
            'item_id': app.id, 
            'type': 'appointment', 
            'date': app.appointment_date.date(),
            'customer_name': app.customer.name,
            'customer_phone': app.customer.phone,
            'service_name': "Không phát sinh dịch vụ (Fail)",
            'service_id': "",
            'consultant': app.assigned_consultant,
            'telesale': app.customer.assigned_telesale,
            'total_amount': 0
        })
        
    order_logs.sort(key=lambda x: x['date'], reverse=True)

    # --- 4. TÍNH HIỆU SUẤT SALE ---
    revenue_data = {}
    # Tính biểu đồ bằng vòng lặp an toàn
    for o in orders_list:
        d = o.order_date
        if d: 
            rev = safe_float(o.actual_revenue)
            revenue_data[d] = revenue_data.get(d, 0) + rev
    
    sorted_dates = sorted(revenue_data.keys())
    chart_dates = [d.strftime('%d/%m') for d in sorted_dates]
    chart_revenues = [revenue_data[d] for d in sorted_dates]
    revenue_table = [{'date': d, 'amount': revenue_data[d]} for d in sorted_dates]

    consultants_list = User.objects.filter(role='CONSULTANT')
    if consultant_id and consultant_id != 'none' and consultant_id.isdigit():
        consultants_list = consultants_list.filter(id=consultant_id)
        
    sale_performance_data = []

    for cons in consultants_list:
        apps = Appointment.objects.filter(
            assigned_consultant=cons, 
            appointment_date__date__range=[date_start, date_end]
        )
        assigned_count = apps.count()
        checkin_count = apps.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        
        # Lọc orders của sale này từ list đã lấy
        my_orders = [o for o in orders_list if o.assigned_consultant_id == cons.id]
        
        success_count = apps.filter(status='COMPLETED', order__total_amount__gt=0).distinct().count()
        completed_total = apps.filter(status='COMPLETED').count()
        failed_count = completed_total - success_count
        if failed_count < 0: failed_count = 0
        
        real_orders_count = 0
        revenue_val = 0
        for o in my_orders:
            amt = safe_float(o.total_amount)
            rev = safe_float(o.actual_revenue)
            if amt > 0: real_orders_count += 1
            revenue_val += rev
        
        avg_revenue = 0
        if checkin_count > 0:
            avg_revenue = int(revenue_val / checkin_count)

        if assigned_count > 0 or len(my_orders) > 0:
            sale_performance_data.append({
                'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
                'assigned': assigned_count,
                'checkin': checkin_count,
                'success': success_count,
                'failed': failed_count,
                'total_orders': real_orders_count,
                'revenue': revenue_val,
                'avg_revenue': avg_revenue 
            })
    
    sale_performance_data.sort(key=lambda x: x['revenue'], reverse=True)

    # Thống kê Telesale & Marketing (An toàn)
    telesale_map = {}
    for o in orders_list:
        tele = o.customer.assigned_telesale
        rev = safe_float(o.actual_revenue)
        
        if not tele:
            display_name = 'Không có Telesale'
        else:
            display_name = f"{tele.last_name} {tele.first_name}".strip() or tele.username
            
        telesale_map[display_name] = telesale_map.get(display_name, 0) + rev

    telesale_revenue_table = [{'name': k, 'amount': v} for k, v in sorted(telesale_map.items(), key=lambda item: item[1], reverse=True)]

    doctors = User.objects.filter(role='DOCTOR')
    consultants = User.objects.filter(role='CONSULTANT')
    services = Service.objects.all().order_by('name')
    telesales_list = User.objects.filter(role='TELESALE').order_by('first_name')

    context = {
        'orders': orders, 
        'order_logs': order_logs,
        'total_revenue': total_revenue, 
        'total_sales': total_sales,
        'total_debt': total_debt,
        'total_orders': total_orders_success, 
        'avg_order_value': avg_order_value,
        'chart_dates': chart_dates, 
        'chart_revenues': chart_revenues,
        'sale_performance_data': sale_performance_data,
        'telesale_revenue_table': telesale_revenue_table,
        'revenue_table': revenue_table, 
        'date_start': date_start, 
        'date_end': date_end,
        'selected_doctor': int(doctor_id) if doctor_id else None,
        'selected_consultant': int(consultant_id) if consultant_id and consultant_id.isdigit() else consultant_id,
        'doctors': doctors, 
        'consultants': consultants,
        'services': services, 
        'telesales_list': telesales_list,
    }
    return render(request, 'sales/revenue_dashboard.html', context)

# --- HÀM CẬP NHẬT CHI TIẾT ĐƠN HÀNG (GIỮ NGUYÊN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MANAGER', 'RECEPTIONIST', 'TELESALE'])
def update_order_details(request):
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')
        
        new_consultant_id = request.POST.get('consultant_id')
        new_service_id = request.POST.get('service_id')
        new_total_amount = request.POST.get('total_amount')
        new_date = request.POST.get('order_date')
        new_telesale_id = request.POST.get('telesale_id')
        
        try:
            new_cons = None
            if new_consultant_id: new_cons = User.objects.get(id=new_consultant_id)
            
            new_service = None
            if new_service_id: new_service = Service.objects.get(id=new_service_id)
            
            new_telesale = None
            if new_telesale_id: new_telesale = User.objects.get(id=new_telesale_id)

            target_customer = None

            if item_type == 'order':
                order = Order.objects.get(id=item_id)
                target_customer = order.customer
                
                order.assigned_consultant = new_cons
                if new_service: order.service = new_service
                
                if new_total_amount is not None:
                    # Clean định dạng số an toàn
                    clean_amount = safe_float(new_total_amount)
                    order.total_amount = clean_amount
                    order.actual_revenue = clean_amount 
                
                if new_date: order.order_date = new_date
                order.save()
                
                if order.appointment:
                    order.appointment.assigned_consultant = new_cons
                    order.appointment.save()
                    
                messages.success(request, f"Đã cập nhật chi tiết đơn hàng #{order.id}")
                
            elif item_type == 'appointment':
                appt = Appointment.objects.get(id=item_id)
                target_customer = appt.customer
                appt.assigned_consultant = new_cons
                
                if new_date:
                    original_time = appt.appointment_date.time()
                    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
                    appt.appointment_date = datetime.combine(new_date_obj, original_time)
                
                appt.save()
                messages.success(request, f"Đã cập nhật thông tin lịch hẹn")

            if target_customer and new_telesale_id is not None:
                target_customer.assigned_telesale = new_telesale
                target_customer.save()
                
        except Exception as e:
            messages.error(request, f"Lỗi cập nhật: {str(e)}")
            
    return redirect(request.META.get('HTTP_REFERER', 'sales_report'))

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN', 'TELESALE'])
def print_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Gán lại giá trị an toàn để hiển thị view
    order.safe_total = safe_float(order.total_amount)
    
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
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE'])
def debt_manager(request):
    # Lấy QuerySet gốc
    all_orders = Order.objects.select_related('customer', 'service', 'assigned_consultant').order_by('-order_date')
    
    date_start = request.GET.get('date_start', '')
    date_end = request.GET.get('date_end', '')
    
    d_start = None
    d_end = None
    if date_start and date_end:
        try:
            d_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            d_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError: pass

    search_query = request.GET.get('q', '').strip().lower()
    
    # Lọc thủ công bằng Python để tránh lỗi Decimal
    orders = []
    total_debt = 0
    
    for o in all_orders:
        # Filter ngày
        if d_start and d_end:
            if not (d_start <= o.order_date <= d_end): continue
            
        # Filter tìm kiếm
        if search_query:
            c_name = o.customer.name.lower() if o.customer else ''
            c_phone = o.customer.phone.lower() if o.customer else ''
            c_code = o.customer.customer_code.lower() if o.customer and o.customer.customer_code else ''
            if (search_query not in c_name) and (search_query not in c_phone) and (search_query not in c_code):
                continue
        
        # Kiểm tra nợ > 0
        debt = safe_float(o.debt_amount)
        if debt > 0:
            o.safe_debt = debt # Gán thuộc tính tạm để dùng ở template
            orders.append(o)
            total_debt += debt

    total_count = len(orders)
    
    # Tính biểu đồ nợ theo Sale (Thủ công)
    debt_by_sale = {}
    for o in orders:
        cons = o.assigned_consultant
        if cons:
            name = f"{cons.last_name} {cons.first_name}".strip() or cons.username
        else:
            name = "Chưa gán"
        debt_by_sale[name] = debt_by_sale.get(name, 0) + o.safe_debt
    
    sorted_sale = sorted(debt_by_sale.items(), key=lambda x: x[1], reverse=True)[:5]
    sale_labels = [k for k, v in sorted_sale]
    sale_data = [v for k, v in sorted_sale]

    # Tính biểu đồ nợ theo Ngày
    debt_by_date = {}
    for o in orders:
        d = o.order_date
        debt_by_date[d] = debt_by_date.get(d, 0) + o.safe_debt
        
    sorted_dates = sorted(debt_by_date.keys())
    date_labels = [d.strftime('%d/%m') for d in sorted_dates]
    date_data = [debt_by_date[d] for d in sorted_dates]

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

    # --- TÍNH TOÁN AN TOÀN (KHÔNG DÙNG AGGREGATE) ---
    orders_current = list(Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True))
    orders_prev = list(Order.objects.filter(order_date__range=[previous_start, previous_end], is_paid=True))

    # 1. Doanh thu hiện tại
    revenue_current = 0
    trend_data = {}
    service_map = {}
    telesale_map = {}

    for o in orders_current:
        amt = safe_float(o.total_amount)
        revenue_current += amt
        
        # Biểu đồ xu hướng
        d = o.order_date
        if d: trend_data[d] = trend_data.get(d, 0) + amt
        
        # Top Dịch vụ
        svc = o.service
        svc_name = svc.name if svc else "Khác"
        service_map[svc_name] = service_map.get(svc_name, 0) + amt
        
        # Top Telesale
        tele = o.customer.assigned_telesale if o.customer else None
        tele_name = f"{tele.last_name} {tele.first_name}".strip() if (tele and tele.first_name) else (tele.username if tele else "Không có Telesale")
        telesale_map[tele_name] = telesale_map.get(tele_name, 0) + amt

    # 2. Doanh thu kỳ trước
    revenue_previous = 0
    for o in orders_prev:
        revenue_previous += safe_float(o.total_amount)
    
    growth_rate = 0
    if revenue_previous > 0:
        growth_rate = ((revenue_current - revenue_previous) / revenue_previous) * 100
    elif revenue_current > 0:
        growth_rate = 100

    # 3. Các chỉ số Count (Count ít khi lỗi nên giữ nguyên)
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

    # 4. Sắp xếp dữ liệu biểu đồ
    sorted_trend = sorted(trend_data.keys())
    chart_labels = [d.strftime('%d/%m') for d in sorted_trend]
    chart_data = [trend_data[d] for d in sorted_trend]

    sorted_svc = sorted(service_map.items(), key=lambda x: x[1], reverse=True)[:5]
    service_labels = [k for k, v in sorted_svc]
    service_data = [v for k, v in sorted_svc]

    # 5. Consultant Stats (Thủ công)
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
        
        # Lọc orders từ list cache để tránh query lại
        my_orders = [o for o in orders_current if o.assigned_consultant_id == cons.id]
        rev_filtered = sum(safe_float(o.total_amount) for o in my_orders)
        total_orders_admin = len(my_orders)
        
        avg_revenue = 0
        if checkin > 0:
            avg_revenue = int(rev_filtered / checkin)

        if assigned > 0 or total_orders_admin > 0:
            consultant_stats_filtered.append({
                'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
                'assigned': assigned,
                'checkin': checkin,
                'success': success,
                'failed': failed,
                'total_orders': total_orders_admin,
                'revenue': rev_filtered,
                'avg_revenue': avg_revenue 
            })

    sorted_tele = sorted(telesale_map.items(), key=lambda x: x[1], reverse=True)[:5]
    top_telesales = [{'name': k, 'total': v} for k, v in sorted_tele]

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