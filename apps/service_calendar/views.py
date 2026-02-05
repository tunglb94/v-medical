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
from apps.sales.models import Service # [MỚI] Import Service
from .models import ReminderLog

User = get_user_model()

@login_required(login_url='/auth/login/')
def calendar_dashboard(request):
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    user = request.user

    # --- 1. KHÁCH HÀNG (CỘT TRÁI) ---
    customers_query = Customer.objects.filter(order__is_paid=True).distinct().prefetch_related(
        'order_set', 'order_set__service', 'order_set__assigned_consultant'
    )
    
    q = request.GET.get('q')
    if q:
        customers_query = customers_query.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    customers = []
    for cus in customers_query:
        paid_orders = cus.order_set.filter(is_paid=True)
        service_names = set(o.service.name for o in paid_orders if o.service)
        cus.service_summary = ", ".join(service_names) if service_names else "Chưa rõ"
        customers.append(cus)

    # --- 2. LẤY DỮ LIỆU LỊCH (CỘT PHẢI) ---
    appointments = Appointment.objects.filter(
        Q(assigned_technician__isnull=False) | 
        Q(created_by__role='TECHNICIAN')
    ).exclude(
        created_by__role='TELESALE'
    ).select_related('customer', 'reminder_log', 'assigned_doctor', 'assigned_technician', 'service') # [MỚI] select_related service

    # --- BỘ LỌC TÌM KIẾM ---
    filter_code = request.GET.get('filter_code')
    filter_doctor = request.GET.get('filter_doctor')
    filter_tech = request.GET.get('filter_tech')

    if filter_code:
        appointments = appointments.filter(customer__customer_code__icontains=filter_code)
    if filter_doctor:
        appointments = appointments.filter(assigned_doctor_id=filter_doctor)
    if filter_tech:
        appointments = appointments.filter(assigned_technician_id=filter_tech)
    
    events_list = []
    for appt in appointments:
        color = '#6c757d' 
        if not appt.assigned_technician:
            color = '#ffc107' 
        if appt.assigned_technician_id == user.id:
            color = '#28a745' 
        if appt.status == 'CANCELLED':
            color = '#e74a3b'

        # [MỚI] Hiển thị tên dịch vụ trong tiêu đề lịch
        service_name = appt.service.name if appt.service else "Chưa chọn dịch vụ"
        title = f"{appt.customer.name}\n({service_name})"
        
        doc_name = f"BS. {appt.assigned_doctor.last_name} {appt.assigned_doctor.first_name}" if appt.assigned_doctor else ""
        tech_name = "Chưa gán KTV"
        if appt.assigned_technician:
            tech_name = f"KTV. {appt.assigned_technician.last_name} {appt.assigned_technician.first_name}"

        events_list.append({
            'id': appt.id,
            'title': title,
            'start': appt.appointment_date.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'phone': appt.customer.phone if appt.customer else "",
                'status_code': appt.status,
                'doctor': doc_name,
                'technician': tech_name,
                'service': service_name # [MỚI] Thêm info service
            }
        })

    # --- 3. NHẮC HẸN ---
    reminders_needed = []
    tomorrow_appts = Appointment.objects.filter(
        appointment_date__date=tomorrow, 
        status='SCHEDULED'
    ).filter(
        Q(assigned_technician__isnull=False) | Q(created_by__role='TECHNICIAN')
    ).exclude(
        created_by__role='TELESALE'
    )

    for appt in tomorrow_appts:
        if not hasattr(appt, 'reminder_log') or not appt.reminder_log.is_reminded:
            reminders_needed.append(appt)

    doctors_list = User.objects.filter(role='DOCTOR', is_active=True)
    techs_list = User.objects.filter(role='TECHNICIAN', is_active=True)
    
    # [MỚI] Lấy danh sách dịch vụ
    services_list = Service.objects.all().order_by('name')

    context = {
        'customers': customers,
        'events': json.dumps(events_list),
        'reminders_needed': reminders_needed,
        'doctors': doctors_list,
        'technicians': techs_list,
        'services': services_list, # [MỚI] Truyền xuống template
        'search_query': q,
        'filter_code': filter_code,
        'filter_doctor': filter_doctor,
        'filter_tech': filter_tech,
    }
    return render(request, 'service_calendar/dashboard.html', context)

@login_required
def get_service_events(request):
    return calendar_dashboard(request)

@login_required
def quick_add_appointment(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        doctor_id = request.POST.get('doctor_id')
        service_id = request.POST.get('service_id') # [MỚI] Lấy ID dịch vụ
        note = request.POST.get('note') # [MỚI] Lấy ghi chú
        dates = request.POST.getlist('dates[]')
        times = request.POST.getlist('times[]')
        
        if not customer_id or not dates:
            messages.error(request, "Thiếu thông tin.")
            return redirect('service_calendar:dashboard')

        customer = get_object_or_404(Customer, id=customer_id)
        count = 0
        for d, t in zip(dates, times):
            if d and t:
                # [MỚI] Tạo lịch kèm dịch vụ và ghi chú
                Appointment.objects.create(
                    customer=customer,
                    appointment_date=f"{d} {t}",
                    assigned_doctor_id=doctor_id if doctor_id else None,
                    service_id=service_id if service_id else None, # Lưu dịch vụ
                    note=note if note else "", # Lưu ghi chú
                    assigned_technician=request.user,
                    created_by=request.user,
                    status='SCHEDULED'
                )
                count += 1
        messages.success(request, f"Đã tạo {count} lịch hẹn.")
        return redirect('service_calendar:dashboard')
    return redirect('service_calendar:dashboard')

@login_required
def confirm_reminder(request, appt_id):
    appt = get_object_or_404(Appointment, id=appt_id)
    log, created = ReminderLog.objects.get_or_create(appointment=appt)
    log.is_reminded = True
    log.reminded_by = request.user
    log.save()
    messages.success(request, f"Đã xác nhận nhắc lịch.")
    return redirect('service_calendar:dashboard')

@login_required
def update_appointment_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            appt_id = data.get('id')
            new_status = data.get('status')
            reschedule_date = data.get('reschedule_date')

            appt = Appointment.objects.get(id=appt_id)
            appt.status = new_status
            appt.save()

            message = "Đã cập nhật trạng thái."

            if new_status == 'CANCELLED' and reschedule_date:
                # [MỚI] Khi dời lịch, copy cả dịch vụ sang lịch mới
                Appointment.objects.create(
                    customer=appt.customer,
                    appointment_date=reschedule_date,
                    assigned_doctor=appt.assigned_doctor,
                    assigned_technician=appt.assigned_technician,
                    service=appt.service, # Copy service
                    note=appt.note,       # Copy note
                    created_by=request.user,
                    status='SCHEDULED'
                )
                message = "Đã hủy và tạo lịch mới."

            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid method'})