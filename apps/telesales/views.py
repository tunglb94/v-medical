from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from apps.customers.models import Customer
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- 1. DASHBOARD TELESALE ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE'])
def telesale_dashboard(request):
    today = timezone.now().date()
    
    # --- LỌC DỮ LIỆU ---
    customers = Customer.objects.all()

    # 1. Tìm kiếm
    search_query = request.GET.get('q', '')
    if search_query:
        customers = customers.filter(
            Q(phone__icontains=search_query) | Q(name__icontains=search_query)
        )

    # 2. Lọc Khách Mới / Khách Cũ
    filter_type = request.GET.get('type', 'new') 
    if filter_type == 'new':
        customers = customers.filter(created_at__date=today)
    elif filter_type == 'old':
        customers = customers.exclude(created_at__date=today)
    
    customers = customers.order_by('-created_at')

    # --- XỬ LÝ CHỌN KHÁCH (FIX LỖI ID RÁC) ---
    selected_customer = None
    call_history = []
    
    customer_id = request.GET.get('id')
    if customer_id:
        try:
            # Chỉ lấy ID nếu là số hợp lệ
            clean_id = int(float(str(customer_id).replace(',', '.')))
            selected_customer = get_object_or_404(Customer, id=clean_id)
        except (ValueError, TypeError, Customer.DoesNotExist):
            # Nếu ID rác (vd: 1.389, text...), bỏ qua không chọn khách nào
            pass
    elif customers.exists():
        selected_customer = customers.first()

    if selected_customer:
        call_history = CallLog.objects.filter(customer=selected_customer).order_by('-call_time')

    # --- XỬ LÝ LƯU CUỘC GỌI (POST) ---
    if request.method == "POST" and selected_customer:
        note_content = request.POST.get('note')
        status_value = request.POST.get('status')
        appointment_date = request.POST.get('appointment_date')
        telesale_id = request.POST.get('telesale_id')
        
        caller_user = request.user
        if telesale_id:
            try:
                caller_user = User.objects.get(id=telesale_id)
            except User.DoesNotExist:
                pass

        if status_value == 'BOOKED':
            if not appointment_date:
                messages.error(request, "LỖI: Phải chọn Ngày/Giờ để đặt lịch!")
                return redirect(f'/?id={selected_customer.id}&type={filter_type}&q={search_query}')
            
            Appointment.objects.create(
                customer=selected_customer,
                appointment_date=appointment_date,
                status='SCHEDULED',
                created_by=caller_user
            )
            messages.success(request, f"Đã đặt lịch: {selected_customer.name}")

        CallLog.objects.create(
            customer=selected_customer,
            caller=caller_user,
            status=status_value,
            note=note_content
        )
        
        if status_value != 'BOOKED':
            messages.info(request, "Đã lưu kết quả.")

        return redirect(f'/?id={selected_customer.id}&type={filter_type}&q={search_query}')

    staff_users = User.objects.filter(is_active=True).order_by('username')

    context = {
        'customers': customers,
        'selected_customer': selected_customer,
        'call_history': call_history,
        'staff_users': staff_users,
        'search_query': search_query,
        'filter_type': filter_type,
    }
    return render(request, 'telesales/dashboard.html', context)


# --- 2. THÊM KHÁCH HÀNG NHANH ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE'])
def add_customer_manual(request):
    if request.method == "POST":
        phone = request.POST.get('phone')
        name = request.POST.get('name')
        
        if not phone or not name:
            messages.error(request, "Thiếu tên hoặc SĐT!")
            return redirect('home')

        if Customer.objects.filter(phone=phone).exists():
            messages.error(request, f"SĐT {phone} đã tồn tại!")
            return redirect('home')

        try:
            new_customer = Customer.objects.create(
                name=name, 
                phone=phone,
                dob=request.POST.get('dob') or None,
                city=request.POST.get('city'),
                address=request.POST.get('address'),
                source=request.POST.get('source'),
                skin_condition=request.POST.get('skin_condition'),
                note_telesale=request.POST.get('note_telesale')
            )
            messages.success(request, f"Đã thêm khách: {name}")
            return redirect(f'/?id={new_customer.id}')
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            
    return redirect('home')