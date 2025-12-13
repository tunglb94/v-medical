from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from apps.bookings.models import Appointment
from apps.customers.models import Customer
from apps.sales.models import Order, Service
from apps.telesales.models import CallLog
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- 1. DASHBOARD LỄ TÂN ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'TELESALE', 'ADMIN']) 
def reception_dashboard(request):
    today = timezone.now().date()
    
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        current_date = parse_date(selected_date_str) or today
    else:
        current_date = today
    
    appointments = Appointment.objects.filter(
        appointment_date__date=current_date
    ).select_related('customer').order_by('status', 'appointment_date')

    birthdays_today = Customer.objects.filter(dob__day=today.day, dob__month=today.month)

    doctors = User.objects.filter(role='DOCTOR')
    technicians = User.objects.filter(role='TECHNICIAN')
    consultants = User.objects.filter(role='CONSULTANT')
    
    services = Service.objects.order_by('name')

    search_query = request.GET.get('q', '')
    search_results = []
    if search_query:
        search_results = Customer.objects.filter(
            Q(name__icontains=search_query) | Q(phone__icontains=search_query)
        )[:10]

    context = {
        'appointments': appointments,
        'birthdays_today': birthdays_today,
        'current_date': current_date,
        'today': today,
        'doctors': doctors,
        'technicians': technicians,
        'consultants': consultants,
        'services': services,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'bookings/reception_dashboard.html', context)


# --- 2. API LẤY DỮ LIỆU CHO LỊCH (FULLCALENDAR) ---
@login_required(login_url='/auth/login/')
def get_appointments_api(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    events = []
    if start_date and end_date:
        appointments = Appointment.objects.filter(
            appointment_date__range=[start_date[:10], end_date[:10]]
        ).select_related('customer')

        for app in appointments:
            color = '#6c757d'
            if app.status == 'SCHEDULED': color = '#0d6efd'
            elif app.status == 'ARRIVED': color = '#ffc107'
            elif app.status == 'COMPLETED': color = '#198754'
            elif app.status in ['CANCELLED', 'NO_SHOW']: color = '#dc3545'
            
            events.append({
                'id': app.id,
                'title': f"{app.customer.name} ({app.customer.phone})",
                'start': app.appointment_date.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'customerName': app.customer.name,
                    'phone': app.customer.phone,
                    'status': app.get_status_display(),
                    'statusCode': app.status,
                    'customerCode': app.customer.customer_code or '', 
                    'doctor': app.assigned_doctor.last_name if app.assigned_doctor else "Chưa gán"
                }
            })
            
    return JsonResponse(events, safe=False)


# --- 3. CHECK-IN ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'TELESALE', 'ADMIN'])
def checkin_appointment(request, appointment_id):
    app = get_object_or_404(Appointment.objects.select_related('customer'), pk=appointment_id)

    if request.method == "POST":
        customer_code = request.POST.get('customer_code', '').strip()
        
        if app.status == 'SCHEDULED':
            if customer_code:
                if Customer.objects.filter(customer_code=customer_code).exclude(pk=app.customer.pk).exists():
                    messages.error(request, f"LỖI: Mã khách hàng '{customer_code}' đã được sử dụng cho khách hàng khác.")
                    return redirect('reception_home') 
                customer = app.customer
                customer.customer_code = customer_code
                customer.save()

            app.status = 'ARRIVED' 
            app.receptionist = request.user
            app.checkin_time = timezone.now()
            app.save()
            messages.success(request, f"Đã Check-in thành công: {app.customer.name}")
        
        return redirect('reception_home')
    
    if app.status == 'SCHEDULED':
        app.status = 'ARRIVED' 
        app.receptionist = request.user
        app.save()
        messages.success(request, f"Đã Check-in: {app.customer.name}")
        
    return redirect('reception_home')


# --- 4. TẠO LỊCH NHANH ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'TELESALE', 'ADMIN'])
def create_appointment_reception(request):
    if request.method == "POST":
        customer_id = request.POST.get('customer_id')
        appt_date = request.POST.get('appointment_date')
        try:
            Appointment.objects.create(
                customer_id=customer_id,
                appointment_date=appt_date,
                status='SCHEDULED',
                created_by=request.user
            )
            messages.success(request, "Đã lên lịch hẹn thành công")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
    return redirect('reception_home')


# --- 5. KHÁCH VÃNG LAI ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN'])
def add_walkin_appointment(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        appt_date = request.POST.get('appointment_date')
        city = request.POST.get('city')
        
        if not name or not phone:
            messages.error(request, "Thiếu Tên hoặc SĐT!")
            return redirect('reception_home')

        try:
            customer, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={
                    'name': name,
                    'dob': None, 
                    'city': city,
                    'source': 'OTHER',
                    'address': 'Khách vãng lai tại quầy'
                }
            )
            Appointment.objects.create(
                customer=customer,
                appointment_date=appt_date,
                status='ARRIVED',
                created_by=request.user,
                receptionist=request.user
            )
            messages.success(request, f"Đã tiếp nhận khách vãng lai: {name}")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            
    return redirect('reception_home')


# --- 6. CHỐT CA ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN'])
def finish_appointment(request):
    if request.method == "POST":
        appt_id = request.POST.get('appointment_id')
        
        doctor_id = request.POST.get('doctor_id') or None
        technician_id = request.POST.get('technician_id') or None
        consultant_id = request.POST.get('consultant_id') or None
        
        result_status = request.POST.get('result_status')
        
        try:
            if not appt_id:
                raise ValueError("Không tìm thấy ID lịch hẹn")

            appt = Appointment.objects.get(id=appt_id)
            
            if doctor_id: appt.assigned_doctor_id = doctor_id
            if technician_id: appt.assigned_technician_id = technician_id
            if consultant_id: appt.assigned_consultant_id = consultant_id
            
            appt.status = 'COMPLETED'
            appt.save()

            if result_status == 'buy':
                service_id = request.POST.get('service_id')
                original_price = request.POST.get('original_price') or 0
                actual_revenue = request.POST.get('actual_revenue')
                total_amount = request.POST.get('total_amount')
                
                if not total_amount:
                    messages.error(request, "Vui lòng nhập số tiền Tổng đơn hàng!")
                    return redirect('reception_home')
                
                if not actual_revenue:
                    actual_revenue = total_amount
                
                service_obj = None
                service_name = "Dịch vụ khác"
                if service_id:
                    service_obj = Service.objects.get(id=service_id)
                    service_name = service_obj.name

                Order.objects.create(
                    customer=appt.customer,
                    appointment=appt,
                    assigned_consultant_id=consultant_id,
                    service=service_obj,
                    original_price=original_price, 
                    actual_revenue=actual_revenue,
                    total_amount=total_amount,
                    is_paid=True,
                    note=f"Chốt đơn ngày {timezone.now().date()}"
                )
                
                CallLog.objects.create(
                    customer=appt.customer, caller=request.user, status='BOOKED',
                    note=f"Đã mua: {service_name}. Tổng: {total_amount}. Thực thu: {actual_revenue}"
                )
                messages.success(request, f"✅ Đã chốt đơn: {service_name}. Thực thu: {actual_revenue}")
            else:
                reason = request.POST.get('rejection_reason') or "Không mua"
                CallLog.objects.create(
                    customer=appt.customer, caller=request.user, status='NOT_INTERESTED',
                    note=f"TỪ CHỐI TẠI QUẦY: {reason}"
                )
                messages.warning(request, "Đã ghi nhận từ chối.")

        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")

    return redirect('reception_home')