from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, CharField
from django.db.models.functions import Cast
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import Http404

from apps.sales.models import Order, Service
from apps.customers.models import Customer
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- BỘ CÔNG CỤ XỬ LÝ DỮ LIỆU AN TOÀN ---
def safe_float(value):
    if value is None: return 0.0
    try:
        if isinstance(value, (int, float)): return float(value)
        clean_val = str(value).replace(',', '').strip()
        if not clean_val: return 0.0
        return float(clean_val)
    except: return 0.0

def get_safe_orders(queryset):
    return queryset.annotate(
        txt_total=Cast('total_amount', CharField()),
        txt_revenue=Cast('actual_revenue', CharField()),
        txt_debt=Cast('debt_amount', CharField())
    ).defer('total_amount', 'actual_revenue', 'debt_amount')

def hydrate_orders(orders_list):
    for o in orders_list:
        o.total_amount = safe_float(getattr(o, 'txt_total', 0))
        o.actual_revenue = safe_float(getattr(o, 'txt_revenue', 0))
        o.debt_amount = safe_float(getattr(o, 'txt_debt', 0))
        o.safe_total = o.total_amount
        o.safe_revenue = o.actual_revenue
        o.safe_debt = o.debt_amount
    return orders_list

# --- 1. [MỚI] VIEW CẤU HÌNH HOA HỒNG (CHỈ ADMIN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def service_commission_config(request):
    services = Service.objects.all().order_by('name')

    if request.method == 'POST':
        try:
            # Lặp qua các input từ form để cập nhật
            for key, value in request.POST.items():
                if key.startswith('rate_'):
                    service_id = key.split('_')[1]
                    try:
                        rate_val = float(value)
                        # Cập nhật vào DB
                        Service.objects.filter(id=service_id).update(commission_rate=rate_val)
                    except ValueError:
                        continue
            
            messages.success(request, "Đã cập nhật bảng hoa hồng thành công!")
            return redirect('service_commission_config')
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")

    return render(request, 'sales/service_commission_config.html', {
        'services': services
    })

# ---------------------------------------------------------

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'CONSULTANT', 'TELESALE'])
def revenue_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    
    doctor_id = request.GET.get('doctor_id')
    consultant_id = request.GET.get('consultant_id')
    telesale_id = request.GET.get('telesale_id')

    orders_qs = Order.objects.filter(
        order_date__range=[date_start, date_end]
    ).select_related('customer__assigned_telesale', 'service', 'assigned_consultant', 'appointment__assigned_technician')

    if doctor_id: orders_qs = orders_qs.filter(appointment__assigned_doctor_id=doctor_id)
    if consultant_id: 
        if consultant_id == 'none': orders_qs = orders_qs.filter(assigned_consultant__isnull=True)
        elif consultant_id.isdigit(): orders_qs = orders_qs.filter(assigned_consultant_id=consultant_id)
    if telesale_id:
        if telesale_id == 'none': orders_qs = orders_qs.filter(customer__assigned_telesale__isnull=True)
        elif telesale_id.isdigit(): orders_qs = orders_qs.filter(customer__assigned_telesale_id=telesale_id)

    orders = hydrate_orders(list(get_safe_orders(orders_qs)))

    total_sales = 0
    total_revenue = 0
    total_debt = 0
    total_orders_success = 0
    booked_appointment_ids = []

    # --- [MỚI] TÍNH TOÁN HOA HỒNG KTV ---
    ktv_commission_map = {}

    for o in orders:
        total_sales += o.total_amount
        total_revenue += o.actual_revenue
        total_debt += o.debt_amount
        if o.total_amount > 0:
            total_orders_success += 1
        
        if o.appointment_id:
            booked_appointment_ids.append(o.appointment_id)

        # Logic tính hoa hồng KTV
        if o.appointment and o.appointment.assigned_technician:
            ktv = o.appointment.assigned_technician
            ktv_name = f"{ktv.last_name} {ktv.first_name}".strip() or ktv.username
            
            # Lấy % từ Dịch vụ (Lấy trực tiếp từ DB)
            rate_percent = 0
            if o.service:
                rate_percent = float(o.service.commission_rate) # Ví dụ: 0.5, 1, 5
            
            # Tính tiền: Thực thu * (% / 100)
            commission_amount = float(o.actual_revenue) * (rate_percent / 100)
            
            if ktv_name not in ktv_commission_map:
                ktv_commission_map[ktv_name] = {
                    'name': ktv_name,
                    'total_revenue': 0,
                    'total_commission': 0,
                    'order_count': 0,
                }
            
            ktv_commission_map[ktv_name]['total_revenue'] += o.actual_revenue
            ktv_commission_map[ktv_name]['total_commission'] += commission_amount
            ktv_commission_map[ktv_name]['order_count'] += 1

    ktv_commission_table = sorted(ktv_commission_map.values(), key=lambda x: x['total_commission'], reverse=True)
    avg_order_value = int(total_sales / total_orders_success) if total_orders_success > 0 else 0

    # Lấy Ca thất bại
    failed_apps = Appointment.objects.filter(
        appointment_date__date__range=[date_start, date_end],
        status='COMPLETED'
    ).exclude(id__in=booked_appointment_ids).select_related('customer', 'assigned_consultant', 'customer__assigned_telesale')

    if doctor_id: failed_apps = failed_apps.filter(assigned_doctor_id=doctor_id)
    if consultant_id:
        if consultant_id == 'none': failed_apps = failed_apps.filter(assigned_consultant__isnull=True)
        elif consultant_id.isdigit(): failed_apps = failed_apps.filter(assigned_consultant_id=consultant_id)
    if telesale_id:
        if telesale_id == 'none': failed_apps = failed_apps.filter(customer__assigned_telesale__isnull=True)
        elif telesale_id.isdigit(): failed_apps = failed_apps.filter(customer__assigned_telesale_id=telesale_id)

    # Gộp Log
    order_logs = []
    for o in orders:
        order_logs.append({
            'is_fail': (o.total_amount == 0),
            'id': o.id, 'item_id': o.id, 'type': 'order', 'date': o.order_date,
            'customer_name': o.customer.name, 'customer_phone': o.customer.phone,
            'service_name': o.service.name if o.service else "Khác",
            'service_id': o.service.id if o.service else "",
            'consultant': o.assigned_consultant, 'telesale': o.customer.assigned_telesale,
            'total_amount': o.total_amount
        })
        
    for app in failed_apps:
        hidden_order = getattr(app, 'order', None)
        fail_reason = "Không phát sinh dịch vụ (Fail)"
        if hidden_order:
            if hidden_order.total_amount == 0: fail_reason = "Đơn hàng 0đ (Hủy/Lỗi)"
            else: fail_reason = f"Đơn hàng lệch ngày/Lọc ẩn ({hidden_order.order_date})"

        order_logs.append({
            'is_fail': True, 'id': app.id, 'item_id': app.id, 'type': 'appointment', 
            'date': app.appointment_date.date(),
            'customer_name': app.customer.name, 'customer_phone': app.customer.phone,
            'service_name': fail_reason, 'service_id': "",
            'consultant': app.assigned_consultant, 'telesale': app.customer.assigned_telesale,
            'total_amount': 0
        })
    order_logs.sort(key=lambda x: x['date'], reverse=True)

    # Biểu đồ & Bảng
    revenue_data = {}
    for o in orders:
        d = o.order_date
        if d: revenue_data[d] = revenue_data.get(d, 0) + o.actual_revenue
    
    sorted_dates = sorted(revenue_data.keys())
    chart_dates = [d.strftime('%d/%m') for d in sorted_dates]
    chart_revenues = [revenue_data[d] for d in sorted_dates]
    revenue_table = [{'date': d, 'amount': revenue_data[d]} for d in sorted_dates]

    # Hiệu suất Sale
    consultants_list = User.objects.filter(role='CONSULTANT')
    if consultant_id and consultant_id.isdigit():
        consultants_list = consultants_list.filter(id=consultant_id)
        
    sale_performance_data = []
    for cons in consultants_list:
        apps = Appointment.objects.filter(assigned_consultant=cons, appointment_date__date__range=[date_start, date_end])
        if telesale_id:
            if telesale_id == 'none': apps = apps.filter(customer__assigned_telesale__isnull=True)
            elif telesale_id.isdigit(): apps = apps.filter(customer__assigned_telesale_id=telesale_id)

        assigned_count = apps.count()
        checkin_count = apps.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        
        my_orders = [o for o in orders if o.assigned_consultant_id == cons.id]
        
        success_count = apps.filter(status='COMPLETED', order__total_amount__gt=0).count()
        failed_count = max(0, apps.filter(status='COMPLETED').count() - success_count)
        
        rev_val = sum(o.actual_revenue for o in my_orders)
        real_orders = sum(1 for o in my_orders if o.total_amount > 0)
        
        if assigned_count > 0 or len(my_orders) > 0:
            sale_performance_data.append({
                'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
                'assigned': assigned_count, 'checkin': checkin_count,
                'success': success_count, 'failed': failed_count,
                'total_orders': real_orders, 'revenue': rev_val,
                'avg_revenue': int(rev_val / checkin_count) if checkin_count > 0 else 0
            })
    sale_performance_data.sort(key=lambda x: x['revenue'], reverse=True)

    # Telesale Stat
    telesale_map = {}
    for o in orders:
        tele = o.customer.assigned_telesale
        name = f"{tele.last_name} {tele.first_name}".strip() if (tele and tele.first_name) else (tele.username if tele else "Không có Telesale")
        telesale_map[name] = telesale_map.get(name, 0) + o.actual_revenue
    
    telesale_revenue_table = [{'name': k, 'amount': v} for k, v in sorted(telesale_map.items(), key=lambda x: x[1], reverse=True)]

    # Prepare context data
    doctors = User.objects.filter(role='DOCTOR')
    consultants = User.objects.filter(role='CONSULTANT')
    services = Service.objects.all().order_by('name')
    telesales_list = User.objects.filter(role='TELESALE').order_by('first_name')

    context = {
        'orders': orders, 'order_logs': order_logs,
        'total_revenue': total_revenue, 'total_sales': total_sales, 'total_debt': total_debt,
        'total_orders': total_orders_success, 'avg_order_value': avg_order_value,
        'chart_dates': chart_dates, 'chart_revenues': chart_revenues,
        'sale_performance_data': sale_performance_data, 'telesale_revenue_table': telesale_revenue_table,
        'ktv_commission_table': ktv_commission_table, # [MỚI] Bảng hoa hồng KTV
        'revenue_table': revenue_table, 
        'date_start': date_start, 'date_end': date_end,
        'selected_doctor': int(doctor_id) if doctor_id else None,
        'selected_consultant': int(consultant_id) if consultant_id and consultant_id.isdigit() else consultant_id,
        'selected_telesale': int(telesale_id) if telesale_id and telesale_id.isdigit() else telesale_id,
        'doctors': doctors, 
        'consultants': consultants,
        'services': services, 
        'telesales_list': telesales_list,
    }
    return render(request, 'sales/revenue_dashboard.html', context)

# ... (Các hàm update_order_details, print_invoice, debt_manager, admin_dashboard giữ nguyên) ...
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MANAGER', 'RECEPTIONIST', 'TELESALE', 'CONSULTANT'])
def update_order_details(request):
    if request.method == "POST":
        try:
            item_id = request.POST.get('item_id')
            item_type = request.POST.get('item_type')
            
            if item_type == 'order':
                qs = Order.objects.filter(id=item_id)
                safe_qs = get_safe_orders(qs)
                if not safe_qs.exists(): raise Exception("Không tìm thấy đơn hàng")
                order = safe_qs.first()
                hydrate_orders([order])
                
                new_cons_id = request.POST.get('consultant_id')
                new_svc_id = request.POST.get('service_id')
                if new_cons_id: order.assigned_consultant_id = new_cons_id
                if new_svc_id: order.service_id = new_svc_id
                
                new_amount = request.POST.get('total_amount')
                if new_amount is not None:
                    clean_amt = safe_float(new_amount)
                    order.total_amount = clean_amt
                    order.actual_revenue = clean_amt
                
                new_date = request.POST.get('order_date')
                if new_date: order.order_date = new_date
                
                order.save()
                
                if order.appointment:
                    if new_cons_id: 
                        order.appointment.assigned_consultant_id = new_cons_id
                        order.appointment.save()
                
                messages.success(request, f"Đã cập nhật đơn hàng #{order.id}")
                target_customer = order.customer

            elif item_type == 'appointment':
                appt = Appointment.objects.get(id=item_id)
                new_cons_id = request.POST.get('consultant_id')
                if new_cons_id: appt.assigned_consultant_id = new_cons_id
                
                new_date = request.POST.get('order_date')
                if new_date:
                    original_time = appt.appointment_date.time()
                    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
                    appt.appointment_date = datetime.combine(new_date_obj, original_time)
                
                appt.save()
                messages.success(request, f"Đã cập nhật lịch hẹn")
                target_customer = appt.customer

            new_tele_id = request.POST.get('telesale_id')
            if target_customer and new_tele_id is not None:
                if new_tele_id == "": target_customer.assigned_telesale = None
                else: target_customer.assigned_telesale_id = new_tele_id
                target_customer.save()

        except Exception as e:
            messages.error(request, f"Lỗi cập nhật: {e}")
            
    return redirect(request.META.get('HTTP_REFERER', 'sales_report'))

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN', 'TELESALE', 'CONSULTANT'])
def print_invoice(request, order_id):
    qs = Order.objects.filter(id=order_id)
    safe_qs = get_safe_orders(qs)
    if not safe_qs.exists(): raise Http404("Đơn hàng không tồn tại")
    order = safe_qs.first()
    hydrate_orders([order])
    return render(request, 'sales/invoice_print.html', {
        'order': order, 
        'now': timezone.now(),
        'clinic_info': {'name': 'PHÒNG KHÁM THẨM MỸ V-MEDICAL', 'address': '57A Trần Quốc Thảo...', 'hotline': '0943 847 799'}
    })

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE', 'CONSULTANT'])
def debt_manager(request):
    qs = Order.objects.select_related('customer', 'service', 'assigned_consultant').order_by('-order_date')
    orders_all = hydrate_orders(list(get_safe_orders(qs)))
    
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
    
    for o in orders_all:
        if d_start and d_end and not (d_start <= o.order_date <= d_end): continue
        if search_query:
            if (search_query not in (o.customer.name or '').lower()) and (search_query not in (o.customer.phone or '').lower()):
                continue
        if o.debt_amount > 0:
            filtered_orders.append(o)
            total_debt += o.debt_amount

    debt_by_sale = {}
    debt_by_date = {}
    for o in filtered_orders:
        cons = o.assigned_consultant
        name = f"{cons.last_name} {cons.first_name}".strip() if (cons and cons.first_name) else (cons.username if cons else "Chưa gán")
        debt_by_sale[name] = debt_by_sale.get(name, 0) + o.debt_amount
        debt_by_date[o.order_date] = debt_by_date.get(o.order_date, 0) + o.debt_amount

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
    doctors = User.objects.filter(role='DOCTOR')
    consultants = User.objects.filter(role='CONSULTANT')
    services = Service.objects.all().order_by('name')
    telesales_list = User.objects.filter(role='TELESALE').order_by('first_name')

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

    qs_current = Order.objects.filter(order_date__range=[date_start, date_end], is_paid=True)
    orders_current = hydrate_orders(list(get_safe_orders(qs_current)))
    
    qs_prev = Order.objects.filter(order_date__range=[prev_start, prev_end], is_paid=True)
    orders_prev = hydrate_orders(list(get_safe_orders(qs_prev)))

    revenue_current = 0
    trend_data = {}
    service_map = {}
    telesale_map = {}

    for o in orders_current:
        revenue_current += o.total_amount
        if o.order_date: trend_data[o.order_date] = trend_data.get(o.order_date, 0) + o.total_amount
        svc_name = o.service.name if o.service else "Khác"
        service_map[svc_name] = service_map.get(svc_name, 0) + o.total_amount
        tele = o.customer.assigned_telesale if o.customer else None
        tele_name = f"{tele.last_name} {tele.first_name}".strip() if (tele and tele.first_name) else (tele.username if tele else "Không có Telesale")
        telesale_map[tele_name] = telesale_map.get(tele_name, 0) + o.total_amount

    revenue_previous = sum(o.total_amount for o in orders_prev)
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

    consultant_stats_filtered = []
    for cons in consultants:
        apps_filtered = Appointment.objects.filter(assigned_consultant=cons, appointment_date__date__range=[date_start, date_end])
        assigned = apps_filtered.count()
        checkin = apps_filtered.filter(status__in=['ARRIVED', 'IN_CONSULTATION', 'COMPLETED']).count()
        success = apps_filtered.filter(status='COMPLETED', order__isnull=False).distinct().count()
        failed = apps_filtered.filter(status='COMPLETED', order__isnull=True).count()
        
        my_orders = [o for o in orders_current if o.assigned_consultant_id == cons.id]
        rev_filtered = sum(o.total_amount for o in my_orders)
        
        if assigned > 0 or len(my_orders) > 0:
            consultant_stats_filtered.append({
                'name': f"{cons.last_name} {cons.first_name}".strip() or cons.username,
                'assigned': assigned, 'checkin': checkin, 'success': success,
                'failed': failed, 'total_orders': len(my_orders), 'revenue': rev_filtered,
                'avg_revenue': int(rev_filtered / checkin) if checkin > 0 else 0
            })

    qs_recent = Order.objects.filter(order_date__range=[date_start, date_end]).order_by('-order_date')[:10]
    recent_orders = hydrate_orders(list(get_safe_orders(qs_recent)))

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