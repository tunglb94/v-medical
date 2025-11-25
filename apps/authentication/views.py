from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

# 1. HÀM ĐĂNG NHẬP
def login_view(request):
    # Nếu người dùng đã đăng nhập từ trước -> Chuyển hướng luôn
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Xác thực tài khoản
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                # --- CHUYỂN HƯỚNG THEO VAI TRÒ ---
                return redirect_based_on_role(user)
            else:
                messages.error(request, "Tài khoản hoặc mật khẩu không đúng.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đăng nhập.")
    else:
        form = AuthenticationForm()

    return render(request, 'authentication/login.html', {'form': form})

# 2. HÀM ĐĂNG XUẤT
def logout_view(request):
    logout(request)
    messages.success(request, "Bạn đã đăng xuất thành công.")
    return redirect('login') # Quay về trang đăng nhập

# 3. LOGIC ĐIỀU HƯỚNG THÔNG MINH (Smart Redirect)
def redirect_based_on_role(user):
    """
    Hàm này quyết định xem user sẽ được đưa đến trang nào
    dựa trên Vai trò (Role) của họ.
    """
    # Admin / Sếp -> Vào Dashboard Tổng Quan
    if user.role == 'ADMIN' or user.is_superuser:
        return redirect('admin_dashboard')
    
    # Lễ tân -> Vào màn hình Lễ tân
    elif user.role == 'RECEPTIONIST':
        return redirect('reception_home')
    
    # Telesale -> Vào màn hình gọi điện (Trang chủ)
    elif user.role == 'TELESALE':
        return redirect('home')
    
    # Bác sĩ / Kỹ thuật viên -> Tạm thời cho vào xem Lịch hẹn (Lễ tân)
    # (Hoặc sau này bạn làm trang riêng cho Bác sĩ thì sửa ở đây)
    elif user.role in ['DOCTOR', 'TECHNICIAN']:
        return redirect('reception_home')
    
    # Mặc định (Sale, khác...) -> Vào trang chủ
    else:
        return redirect('home')