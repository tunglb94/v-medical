from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from apps.authentication.decorators import allowed_users
from .forms import StaffForm

User = get_user_model()

# ... (Giữ nguyên login_view, logout_view, redirect_based_on_role cũ) ...
# ... BẮT ĐẦU ĐOẠN CODE CŨ ...
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
    if user.role == 'ADMIN' or user.is_superuser: return redirect('admin_dashboard')
    elif user.role == 'RECEPTIONIST': return redirect('reception_home')
    elif user.role == 'TELESALE': return redirect('home')
    return redirect('home')
# ... KẾT THÚC ĐOẠN CODE CŨ ...

# --- PHẦN MỚI: QUẢN LÝ NHÂN SỰ ---

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
            messages.success(request, f"Đã lưu thông tin nhân viên: {form.cleaned_data['username']}")
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