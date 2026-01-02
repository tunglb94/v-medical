from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()

# Danh sách các Menu trong hệ thống (Key phải khớp với base.html)
MENU_CHOICES = [
    ('dashboard', 'Dashboard Tổng quan (Admin)'),
    ('telesale', 'Telesale Center'),
    ('reception', 'Lễ tân & Lịch hẹn'),
    ('service_calendar', 'Lịch CS & Nhắc hẹn'),
    ('inventory', 'Kho & Vật tư'),
    ('debt', 'Sổ Theo Dõi Nợ'),
    ('customers', 'Hồ sơ Khách hàng'),
    ('sales_report', 'Báo cáo Doanh thu'),
    ('marketing', 'Marketing & Ads'),
    ('resources', 'Tài liệu & Đào tạo'),
    ('hr', 'Nhân sự (Hợp đồng/Lương)'),
    ('attendance', 'Bảng công'),
    ('chat', 'Chat Nội bộ'),
]

# --- 1. FORM QUẢN LÝ NHÂN SỰ (DÀNH CHO ADMIN) ---
class StaffForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False, 
        label="Mật khẩu (Để trống nếu không đổi)"
    )
    
    # [MỚI] Checkbox chọn Menu
    allowed_menus = forms.MultipleChoiceField(
        choices=MENU_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Phân quyền Menu (Chọn các mục được phép xem)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'team', 'is_active', 'allowed_menus']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'team': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nếu đang sửa user cũ, lấy dữ liệu JSON đưa vào Checkbox
        if self.instance and self.instance.pk:
            self.fields['allowed_menus'].initial = self.instance.allowed_menus

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
            
        # Lưu allowed_menus (Django ModelForm tự xử lý field không có trong model nếu không cẩn thận,
        # nhưng ở đây ta cần gán thủ công hoặc đảm bảo field có trong cleaned_data)
        # Note: Vì allowed_menus là JSONField trong model, Django 3.1+ xử lý khá tốt, 
        # nhưng với MultipleChoiceField ta cần đảm bảo nó lưu dưới dạng list.
        user.allowed_menus = self.cleaned_data.get('allowed_menus', [])
        
        if commit:
            user.save()
        return user

# --- 2. FORM CẬP NHẬT HỒ SƠ CÁ NHÂN (USER TỰ SỬA) ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ đệm'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
        }

# --- 3. FORM ĐỔI MẬT KHẨU ---
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})