from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth import get_user_model

# Import model từ các app khác (chỉ đọc, không sửa code bên kia)
from apps.bookings.models import Appointment
from apps.customers.models import Customer
from apps.sales.models import Order
from .models import ReminderLog # Model riêng của app này

User = get_user_model()

@login_required(login_url='/auth/login/')
def calendar_dashboard(request):
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # 1. CỘT TRÁI: Khách đã từng mua hàng (để đặt lịch tái khám/liệu trình)
    # Logic: Lấy khách có đơn hàng đã thanh toán
    customers = Customer.objects.filter(order__is_paid=True).distinct()
    
    # Tìm kiếm khách
    q = request.GET.get('q')
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    # 2. CỘT PHẢI: Lấy dữ liệu lịch
    appointments = Appointment.objects.exclude(status='CANCELLED').select_related('customer', 'reminder_log')
    
    events = []
    for appt in appointments:
        # Màu sắc: Xanh lá (Đã đến), Xám (Xong), Xanh dương (Chờ), Đỏ (Chưa nhắc - Logic mới)
        color = '#4e73df' # Mặc định
        if appt.status == 'ARRIVED': color = '#1cc88a'
        elif appt.status == 'COMPLETED': color = '#858796'
        
        # Kiểm tra trạng thái nhắc lịch từ bảng phụ
        is_reminded = False
        if hasattr(appt, 'reminder_log') and appt.reminder_log.is_reminded:
            is_reminded = True
        
        # Logic cảnh báo: Lịch ngày mai mà chưa nhắc thì hiện màu vàng cam
        if appt.appointment_date.date() == tomorrow and appt.status == 'SCHEDULED' and not is_reminded:
            color = '#f6c23e'

        events.append({
            'id': appt.id,
            'title': f"{appt.customer.name} - {appt.service_name if hasattr(appt, 'service_name') else 'Hẹn'}",
            'start': appt.appointment_date.isoformat(),
            'backgroundColor': color,
            'extendedProps': {
                'phone': appt.customer.phone,
                'is_reminded': is_reminded
            }
        })

    # 3. DANH SÁCH CẦN NHẮC (Cho ngày mai)
    # Lấy các lịch hẹn ngày mai chưa có log nhắc nhở
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
        'events': events,
        'reminders_needed': reminders_needed,
        'doctors': User.objects.filter(role='DOCTOR'),
        'search_query': q
    }
    return render(request, 'service_calendar/dashboard.html', context)

# API: Lưu lịch mới từ Popup
@login_required
def quick_add_appointment(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        date = request.POST.get('date')
        time = request.POST.get('time')
        doctor_id = request.POST.get('doctor_id')
        note = request.POST.get('note')

        customer = get_object_or_404(Customer, id=customer_id)
        
        # Tạo lịch hẹn (Dùng model cũ)
        appt = Appointment.objects.create(
            customer=customer,
            appointment_date=f"{date} {time}",
            assigned_doctor_id=doctor_id if doctor_id else None,
            created_by=request.user,
            status='SCHEDULED'
        )
        
        # Nếu có ghi chú, có thể tạo luôn ReminderLog hoặc để trống
        return redirect('service_calendar:dashboard')
    return redirect('service_calendar:dashboard')

# API: Xác nhận đã nhắc
@login_required
def confirm_reminder(request, appt_id):
    appt = get_object_or_404(Appointment, id=appt_id)
    # Tạo hoặc cập nhật bản ghi trong ReminderLog
    log, created = ReminderLog.objects.get_or_create(appointment=appt)
    log.is_reminded = True
    log.reminded_by = request.user
    log.save()
    return redirect('service_calendar:dashboard')