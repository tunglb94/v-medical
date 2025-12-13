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
    
    # Lọc theo ngày (mặc định là hôm nay)
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        current_date = parse_date(selected_date_str) or today
    else:
        current_date = today
    
    # Lấy danh sách lịch hẹn trong ngày để hiển thị ở cột bên trái
    appointments = Appointment.objects.filter(
        appointment_date__date=current_date
    ).select_related('customer').order_by('status', 'appointment_date')

    # Sinh nhật hôm nay (Optional features)
    birthdays_today = Customer.objects.filter(dob__day=today.day, dob__month=today.month)

    # Lấy danh sách nhân sự để điền vào Modal Chốt đơn
    doctors = User.objects.filter(role='DOCTOR')
    technicians = User.objects.filter(role='TECHNICIAN')
    consultants = User.objects.filter(role='CONSULTANT')
    
    # Lấy danh sách dịch vụ
    services = Service.objects.order_by('name')

    # Xử lý tìm kiếm nhanh
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
    """
    API trả về dữ liệu JSON cho FullCalendar.
    Lấy tham số start và end do thư viện tự gửi lên.
    """
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    events = []
    if start_date and end_date:
        # Lọc lịch hẹn trong khoảng thời gian đang xem
        appointments = Appointment.objects.filter(
            appointment_date__range=[start_date[:10], end_date[:10]]
        ).select_related('customer', 'assigned_doctor')

        for app in appointments:
            # Quy định màu sắc hiển thị trên lịch
            color = '#6c757d' # Mặc định xám
            if app.status == 'SCHEDULED': color = '#0d6efd'      # Xanh dương (Mới đặt)
            elif app.status == 'ARRIVED': color = '#ffc107'      # Vàng (Đã đến)
            elif app.status == 'IN_CONSULTATION': color = '#17a2b8' # Xanh lơ (Đang làm)
            elif app.status == 'COMPLETED': color = '#198754'    # Xanh lá (Hoàn thành)
            elif app.status in ['CANCELLED', 'NO_SHOW']: color = '#dc3545' # Đỏ (Hủy)
            
            # Tạo object sự kiện đúng chuẩn FullCalendar
            events.append({
                'id': app.id,
                'title': f"{app.customer.name}",
                'start': app.appointment_date.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                # Dữ liệu mở rộng để hiển thị lên Modal chi tiết
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


# --- 3. CHECK-IN (XỬ LÝ NÚT CHECK-IN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'TELESALE', 'ADMIN'])
def checkin_appointment(request, appointment_id):
    """
    Chuyển trạng thái từ SCHEDULED -> ARRIVED.
    Cập nhật mã khách hàng nếu có nhập mới.
    """
    app = get_object_or_404(Appointment.objects.select_related('customer'), pk=appointment_id)

    if request.method == "POST":
        customer_code = request.POST.get('customer_code', '').strip()
        
        # Chỉ check-in nếu trạng thái là Đã đặt
        if app.status == 'SCHEDULED':
            # Cập nhật mã khách hàng nếu có
            if customer_code:
                # Kiểm tra trùng mã
                if Customer.objects.filter(customer_code=customer_code).exclude(pk=app.customer.pk).exists():
                    messages.error(request, f"LỖI: Mã '{customer_code}' đã thuộc về khách hàng khác.")
                    return redirect('reception_home') 
                
                customer = app.customer
                customer.customer_code = customer_code
                customer.save()

            # Cập nhật trạng thái
            app.status = 'ARRIVED' 
            app.receptionist = request.user
            app.save()
            messages.success(request, f"Đã Check-in thành công: {app.customer.name}")
        else:
            messages.warning(request, "Khách hàng này đã được check-in hoặc đã hủy trước đó.")
        
        return redirect('reception_home')
    
    # Nếu truy cập bằng GET (không hợp lệ), quay về trang chủ
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
        
        if not name or not phone:
            messages.error(request, "Vui lòng nhập Tên và SĐT!")
            return redirect('reception_home')

        try:
            # Tìm hoặc tạo mới khách hàng
            customer, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={
                    'name': name,
                    'source': 'OTHER', # Nguồn khác
                    'address': 'Khách vãng lai tại quầy'
                }
            )
            # Tạo lịch hẹn trạng thái Đã đến (ARRIVED) luôn
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


# --- 6. CHỐT CA / KẾT THÚC DỊCH VỤ ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTIONIST', 'ADMIN'])
def finish_appointment(request):
    """
    Xử lý khi kết thúc dịch vụ:
    1. Cập nhật nhân sự (Bác sĩ, KTV, Sale).
    2. Nếu khách mua: Tạo Order -> Doanh thu.
    3. Nếu khách từ chối: Tạo CallLog (ghi chú lý do).
    4. Chuyển trạng thái lịch hẹn -> COMPLETED.
    """
    if request.method == "POST":
        appt_id = request.POST.get('appointment_id')
        
        doctor_id = request.POST.get('doctor_id') or None
        technician_id = request.POST.get('technician_id') or None
        consultant_id = request.POST.get('consultant_id') or None
        
        result_status = request.POST.get('result_status') # 'buy' hoặc 'reject'
        
        try:
            if not appt_id:
                raise ValueError("Không tìm thấy ID lịch hẹn")

            appt = Appointment.objects.get(id=appt_id)
            
            # Cập nhật nhân sự phụ trách vào Lịch hẹn
            if doctor_id: appt.assigned_doctor_id = doctor_id
            if technician_id: appt.assigned_technician_id = technician_id
            if consultant_id: appt.assigned_consultant_id = consultant_id
            
            # Đánh dấu hoàn thành
            appt.status = 'COMPLETED'
            appt.save()

            if result_status == 'buy':
                # --- TRƯỜNG HỢP: KHÁCH MUA ---
                service_id = request.POST.get('service_id')
                original_price = request.POST.get('original_price') or 0
                actual_revenue = request.POST.get('actual_revenue')
                total_amount = request.POST.get('total_amount')
                
                # Validation cơ bản
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

                # Tạo Đơn hàng (Order)
                Order.objects.create(
                    customer=appt.customer,
                    appointment=appt,
                    assigned_consultant_id=consultant_id, # Tính doanh thu cho Sale này
                    service=service_obj,
                    original_price=original_price, 
                    actual_revenue=actual_revenue,
                    total_amount=total_amount,
                    is_paid=True, # Đã thanh toán ngay
                    note=f"Chốt đơn tại quầy ngày {timezone.now().date()}"
                )
                
                # Ghi Log vào lịch sử chăm sóc
                CallLog.objects.create(
                    customer=appt.customer, caller=request.user, status='BOOKED',
                    note=f"Đã mua: {service_name}. Tổng: {total_amount}. Thực thu: {actual_revenue}"
                )
                messages.success(request, f"✅ Đã chốt đơn thành công: {service_name}")
            else:
                # --- TRƯỜNG HỢP: KHÁCH TỪ CHỐI ---
                reason = request.POST.get('rejection_reason') or "Không mua"
                CallLog.objects.create(
                    customer=appt.customer, caller=request.user, status='NOT_INTERESTED',
                    note=f"TỪ CHỐI TẠI QUẦY: {reason}"
                )
                messages.warning(request, "Đã ghi nhận kết quả: Khách từ chối dịch vụ.")

        except Exception as e:
            messages.error(request, f"Lỗi xử lý: {str(e)}")

    return redirect('reception_home')