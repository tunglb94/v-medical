from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from apps.authentication.decorators import allowed_users
from .forms import StaffForm, ProfileUpdateForm, CustomPasswordChangeForm

# --- IMPORTS CHO TÌM KIẾM TOÀN CỤC ---
from django.db.models import Q
from apps.customers.models import Customer
from apps.bookings.models import Appointment

User = get_user_model()

# --- 1. AUTHENTICATION (ĐĂNG NHẬP / ĐĂNG XUẤT / ROOT) ---

def root_view(request):
    """Trang chủ điều hướng (Cổng chính)"""
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect_based_on_role(user)
            else:
                messages.error(request, "Tài khoản hoặc mật khẩu không đúng.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    else:
        form = AuthenticationForm()

    return render(request, 'authentication/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Đã đăng xuất.")
    return redirect('login')

def redirect_based_on_role(user):
    """Điều hướng user đến trang phù hợp với vai trò"""
    if user.role == 'ADMIN' or user.is_superuser:
        return redirect('admin_dashboard')
    
    # THÊM DESIGNER VÀO DANH SÁCH NÀY
    elif user.role in ['MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER']: 
        return redirect('marketing_dashboard')
        
    elif user.role == 'RECEPTIONIST':
        return redirect('reception_home')
        
    elif user.role == 'TELESALE':
        return redirect('telesale_home')
    
    return redirect('user_profile')


# --- 2. QUẢN LÝ NHÂN SỰ (CHỈ ADMIN) ---

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def staff_list(request):
    staffs = User.objects.all().order_by('-is_active', 'role', 'username')
    return render(request, 'authentication/staff_list.html', {'staffs': staffs})

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def staff_create_update(request, pk=None):
    if pk:
        user = get_object_or_404(User, pk=pk)
        title = "Cập nhật nhân viên"
    else:
        user = None
        title = "Thêm nhân viên mới"

    if request.method == 'POST':
        form = StaffForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã lưu thông tin: {form.cleaned_data['username']}")
            return redirect('staff_list')
    else:
        form = StaffForm(instance=user)

    return render(request, 'authentication/staff_form.html', {'form': form, 'title': title})

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def staff_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Không thể xóa tài khoản Super Admin!")
    else:
        user.delete()
        messages.success(request, "Đã xóa nhân viên.")
    return redirect('staff_list')


# --- 3. HỒ SƠ CÁ NHÂN (TẤT CẢ USER) ---

@login_required(login_url='/auth/login/')
def user_profile(request):
    user = request.user
    
    profile_form = ProfileUpdateForm(instance=user)
    password_form = CustomPasswordChangeForm(user=user)

    if request.method == 'POST':
        # Cập nhật thông tin
        if 'btn_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Đã cập nhật thông tin cá nhân!")
                return redirect('user_profile')
            else:
                messages.error(request, "Lỗi cập nhật thông tin.")

        # Đổi mật khẩu
        elif 'btn_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user) # Giữ đăng nhập
                messages.success(request, "Đổi mật khẩu thành công!")
                return redirect('user_profile')
            else:
                messages.error(request, "Mật khẩu không hợp lệ.")

    context = {
        'profile_form': profile_form,
        'password_form': password_form
    }
    return render(request, 'authentication/profile.html', context)

# --- 4. TÌM KIẾM TOÀN CỤC (GLOBAL SEARCH) ---
@login_required(login_url='/auth/login/')
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'customers': [],
        'staffs': [],
        'appointments': []
    }
    
    if query:
        # 1. Tìm Khách hàng (Tên hoặc SĐT)
        # Chỉ Marketing/Admin/Telesale/Receptionist mới được tìm khách
        if request.user.role in ['ADMIN', 'TELESALE', 'RECEPTIONIST', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER']:
            results['customers'] = Customer.objects.filter(
                Q(name__icontains=query) | Q(phone__icontains=query)
            )[:10] # Lấy tối đa 10 kết quả

        # 2. Tìm Nhân viên (Tên hoặc Username)
        results['staffs'] = User.objects.filter(
            Q(username__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(first_name__icontains=query)
        ).exclude(is_active=False)[:5]

        # 3. Tìm Lịch hẹn (Theo mã hoặc tên khách) - Chỉ Admin/Lễ tân/BS
        if request.user.role in ['ADMIN', 'RECEPTIONIST', 'DOCTOR']:
            results['appointments'] = Appointment.objects.filter(
                Q(customer__name__icontains=query) |
                Q(customer__phone__icontains=query)
            ).select_related('customer')[:10]

    return render(request, 'search_results.html', {'query': query, 'results': results})