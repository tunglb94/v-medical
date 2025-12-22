from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib import messages
import json # <--- THÊM IMPORT NÀY ĐỂ XỬ LÝ DỮ LIỆU JS

# Import model từ các app khác
from apps.bookings.models import Appointment
from apps.customers.models import Customer
from apps.sales.models import Order
from .models import ReminderLog

User = get_user_model()

@login_required(login_url='/auth/login/')
def calendar_dashboard(request):
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # 1. CỘT TRÁI: Khách đã từng mua hàng (Order đã thanh toán)
    # Prefetch order_set để tối ưu truy vấn
    customers_query = Customer.objects.filter(order__is_paid=True).distinct().prefetch_related(
        'order_set', 'order_set__service', 'order_set__assigned_consultant'
    )
    
    # Tìm kiếm khách
    q = request.GET.get('q')
    if q:
        customers_query = customers_query.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    # Xử lý dữ liệu hiển thị (Gán thông tin Dịch vụ & Sale vào object customer)
    customers = []
    for cus in customers_query:
        # Lấy các đơn hàng đã thanh toán
        paid_orders = cus.order_set.filter(is_paid=True)
        
        # Lấy danh sách tên dịch vụ (loại bỏ trùng lặp)
        service_names = set(o.service.name for o in paid_orders if o.service)
        cus.service_summary = ", ".join(service_names) if service_names else "Chưa rõ"
        
        # Lấy danh sách Sale (loại bỏ trùng lặp)
        sale_names = set()
        for o in paid_orders:
            if o.assigned_consultant:
                # Ưu tiên lấy Họ tên, nếu không có thì lấy username
                full_name = f"{o.assigned_consultant.last_name} {o.assigned_consultant.first_name}".strip()
                sale_names.add(full_name if full_name else o.assigned_consultant.username)
        
        cus.sale_summary = ", ".join(sale_names) if sale_names else "--"
        
        customers.append(cus)

    # 2. CỘT PHẢI: Lấy dữ liệu lịch
    appointments = Appointment.objects.exclude(status='CANCELLED').select_related('customer', 'reminder_log')
    
    events = []
    for appt in appointments:
        # Màu sắc: Xanh lá (Đã đến), Xám (Xong), Xanh dương (Chờ), Vàng (Cần nhắc)
        color = '#4e73df' # Mặc định: Scheduled
        if appt.status == 'ARRIVED': color = '#1cc88a'
        elif appt.status == 'COMPLETED': color = '#858796'
        elif appt.status == 'NO_SHOW': color = '#e74a3b'
        
        # Kiểm tra trạng thái nhắc lịch
        is_reminded = False
        if hasattr(appt, 'reminder_log') and appt.reminder_log.is_reminded:
            is_reminded = True
        
        # Logic cảnh báo: Lịch ngày mai mà chưa nhắc thì hiện màu vàng
        if appt.appointment_date.date() == tomorrow and appt.status == 'SCHEDULED' and not is_reminded:
            color = '#f6c23e'

        # Tiêu đề hiển thị trên lịch
        title = f"{appt.customer.name}"
        
        events.append({
            'id': appt.id,
            'title': title,
            'start': appt.appointment_date.isoformat(),
            'backgroundColor': color,
            'extendedProps': {
                'phone': appt.customer.phone,
                'status': appt.get_status_display(),
                'is_reminded': is_reminded
            }
        })

    # 3. DANH SÁCH CẦN NHẮC (Cho ngày mai)
    reminders_needed = []
    tomorrow_appts = Appointment.objects.filter(
        appointment_date__date=tomorrow, 
        status='SCHEDULED'
    )
    for appt in tomorrow_appts:
        if not hasattr(appt, 'reminder_log') or not appt.reminder_log.is_reminded:
            reminders_needed.append(appt)

    context = {
        'customers': customers,
        'events': json.dumps(events), # <--- SỬA QUAN TRỌNG: Dump list thành JSON string
        'reminders_needed': reminders_needed,
        'doctors': User.objects.filter(role='DOCTOR'),
        'search_query': q
    }
    return render(request, 'service_calendar/dashboard.html', context)

# API: Lưu nhiều lịch mới cùng lúc
@login_required
def quick_add_appointment(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        doctor_id = request.POST.get('doctor_id')
        
        # Lấy danh sách ngày và giờ (Mảng)
        dates = request.POST.getlist('dates[]')
        times = request.POST.getlist('times[]')
        
        if not customer_id or not dates:
            messages.error(request, "Thiếu thông tin khách hàng hoặc thời gian.")
            return redirect('service_calendar:dashboard')

        customer = get_object_or_404(Customer, id=customer_id)
        count = 0
        
        # Duyệt qua từng cặp Ngày - Giờ để tạo lịch
        for d, t in zip(dates, times):
            if d and t: # Chỉ tạo nếu có đủ ngày giờ
                Appointment.objects.create(
                    customer=customer,
                    appointment_date=f"{d} {t}",
                    assigned_doctor_id=doctor_id if doctor_id else None,
                    created_by=request.user,
                    status='SCHEDULED'
                )
                count += 1
        
        if count > 0:
            messages.success(request, f"Đã tạo thành công {count} lịch hẹn cho khách {customer.name}.")
        else:
            messages.warning(request, "Không có lịch hẹn nào được tạo.")
            
        return redirect('service_calendar:dashboard')
    return redirect('service_calendar:dashboard')

# API: Xác nhận đã nhắc
@login_required
def confirm_reminder(request, appt_id):
    appt = get_object_or_404(Appointment, id=appt_id)
    log, created = ReminderLog.objects.get_or_create(appointment=appt)
    log.is_reminded = True
    log.reminded_by = request.user
    log.save()
    messages.success(request, f"Đã xác nhận nhắc lịch cho {appt.customer.name}")
    return redirect('service_calendar:dashboard')