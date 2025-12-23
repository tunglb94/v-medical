from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
import json 

from apps.bookings.models import Appointment
from apps.customers.models import Customer
from apps.sales.models import Order
from .models import ReminderLog

User = get_user_model()

@login_required(login_url='/auth/login/')
def calendar_dashboard(request):
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # --- 1. CỘT TRÁI: Khách đã từng mua hàng ---
    customers_query = Customer.objects.filter(order__is_paid=True).distinct().prefetch_related(
        'order_set', 'order_set__service', 'order_set__assigned_consultant'
    )
    
    # Tìm kiếm khách (Sidebar)
    q = request.GET.get('q')
    if q:
        customers_query = customers_query.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    customers = []
    for cus in customers_query:
        paid_orders = cus.order_set.filter(is_paid=True)
        service_names = set(o.service.name for o in paid_orders if o.service)
        cus.service_summary = ", ".join(service_names) if service_names else "Chưa rõ"
        
        sale_names = set()
        for o in paid_orders:
            if o.assigned_consultant:
                full_name = f"{o.assigned_consultant.last_name} {o.assigned_consultant.first_name}".strip()
                sale_names.add(full_name if full_name else o.assigned_consultant.username)
        
        cus.sale_summary = ", ".join(sale_names) if sale_names else "--"
        customers.append(cus)

    # --- 2. CỘT PHẢI: Lấy dữ liệu lịch ---
    # Cơ bản: Khách đã mua, không lấy lịch Telesale
    appointments = Appointment.objects.filter(
        customer__order__is_paid=True
    ).exclude(
        created_by__role='TELESALE'
    ).select_related('customer', 'reminder_log', 'assigned_doctor', 'assigned_technician')

    # [MỚI] --- XỬ LÝ BỘ LỌC NÂNG CAO ---
    filter_code = request.GET.get('filter_code')
    filter_doctor = request.GET.get('filter_doctor')
    filter_tech = request.GET.get('filter_tech')

    if filter_code:
        appointments = appointments.filter(customer__customer_code__icontains=filter_code)
    if filter_doctor:
        appointments = appointments.filter(assigned_doctor_id=filter_doctor)
    if filter_tech:
        appointments = appointments.filter(assigned_technician_id=filter_tech)
    # -------------------------------------
    
    events_list = []
    for appt in appointments:
        # Màu sắc theo trạng thái
        color = '#4e73df' # SCHEDULED (Chưa đến - Mặc định)
        if appt.status == 'ARRIVED': color = '#1cc88a' # Đã đến
        elif appt.status == 'CANCELLED': color = '#e74a3b' # Đã hủy
        elif appt.status == 'COMPLETED': color = '#858796' # Hoàn thành
        elif appt.status == 'NO_SHOW': color = '#36b9cc' # Không đến
        
        # Cảnh báo nhắc lịch
        is_reminded = False
        if hasattr(appt, 'reminder_log') and appt.reminder_log.is_reminded:
            is_reminded = True
        
        if appt.appointment_date.date() == tomorrow and appt.status == 'SCHEDULED' and not is_reminded:
            color = '#f6c23e' # Vàng cảnh báo

        title = f"{appt.customer.name}"
        
        # [MỚI] Thêm thông tin bác sĩ/ktv vào props để hiển thị popup
        doc_name = f"BS. {appt.assigned_doctor.last_name} {appt.assigned_doctor.first_name}" if appt.assigned_doctor else ""
        tech_name = f"KTV. {appt.assigned_technician.last_name} {appt.assigned_technician.first_name}" if appt.assigned_technician else ""

        events_list.append({
            'id': appt.id,
            'title': title,
            'start': appt.appointment_date.isoformat(),
            'backgroundColor': color,
            'extendedProps': {
                'phone': appt.customer.phone,
                'status_code': appt.status,          # Mã trạng thái để xử lý logic
                'status_display': appt.get_status_display(), # Tên hiển thị
                'is_reminded': is_reminded,
                'doctor': doc_name,
                'technician': tech_name,
                'note': "" # Có thể thêm field note vào model nếu cần
            }
        })

    # 3. DANH SÁCH CẦN NHẮC
    reminders_needed = []
    tomorrow_appts = Appointment.objects.filter(
        customer__order__is_paid=True,
        appointment_date__date=tomorrow, 
        status='SCHEDULED'
    ).exclude(created_by__role='TELESALE')

    for appt in tomorrow_appts:
        if not hasattr(appt, 'reminder_log') or not appt.reminder_log.is_reminded:
            reminders_needed.append(appt)

    # Lấy danh sách nhân sự cho Dropdown lọc
    doctors_list = User.objects.filter(role='DOCTOR', is_active=True)
    techs_list = User.objects.filter(role='TECHNICIAN', is_active=True)

    context = {
        'customers': customers,
        'events': json.dumps(events_list),
        'reminders_needed': reminders_needed,
        'doctors': doctors_list, # Truyền list bác sĩ
        'technicians': techs_list, # Truyền list KTV
        'search_query': q,
        # Giữ lại giá trị lọc cũ
        'filter_code': filter_code,
        'filter_doctor': filter_doctor,
        'filter_tech': filter_tech,
    }
    return render(request, 'service_calendar/dashboard.html', context)

# --- GIỮ NGUYÊN CÁC HÀM CŨ ---
@login_required
def quick_add_appointment(request):
    # ... (Code cũ giữ nguyên) ...
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        doctor_id = request.POST.get('doctor_id')
        dates = request.POST.getlist('dates[]')
        times = request.POST.getlist('times[]')
        
        if not customer_id or not dates:
            messages.error(request, "Thiếu thông tin.")
            return redirect('service_calendar:dashboard')

        customer = get_object_or_404(Customer, id=customer_id)
        count = 0
        for d, t in zip(dates, times):
            if d and t:
                Appointment.objects.create(
                    customer=customer,
                    appointment_date=f"{d} {t}",
                    assigned_doctor_id=doctor_id if doctor_id else None,
                    created_by=request.user,
                    status='SCHEDULED'
                )
                count += 1
        messages.success(request, f"Đã tạo {count} lịch hẹn.")
        return redirect('service_calendar:dashboard')
    return redirect('service_calendar:dashboard')

@login_required
def confirm_reminder(request, appt_id):
    # ... (Code cũ giữ nguyên) ...
    appt = get_object_or_404(Appointment, id=appt_id)
    log, created = ReminderLog.objects.get_or_create(appointment=appt)
    log.is_reminded = True
    log.reminded_by = request.user
    log.save()
    messages.success(request, f"Đã xác nhận nhắc lịch.")
    return redirect('service_calendar:dashboard')

# --- [MỚI] API CẬP NHẬT TRẠNG THÁI & HẸN LẠI ---
@login_required
def update_appointment_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            appt_id = data.get('id')
            new_status = data.get('status')
            reschedule_date = data.get('reschedule_date') # YYYY-MM-DDTHH:MM format

            appt = Appointment.objects.get(id=appt_id)
            
            # Cập nhật trạng thái
            appt.status = new_status
            appt.save()

            message = "Đã cập nhật trạng thái thành công."

            # Nếu Hủy và có chọn ngày hẹn lại -> Tạo lịch mới
            if new_status == 'CANCELLED' and reschedule_date:
                Appointment.objects.create(
                    customer=appt.customer,
                    appointment_date=reschedule_date,
                    assigned_doctor=appt.assigned_doctor,
                    assigned_technician=appt.assigned_technician,
                    assigned_consultant=appt.assigned_consultant,
                    created_by=request.user,
                    status='SCHEDULED' # Lịch mới mặc định là Chưa đến
                )
                message = "Đã hủy lịch cũ và tạo lịch hẹn lại thành công."

            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid method'})