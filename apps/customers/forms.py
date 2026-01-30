from django import forms
from .models import Customer
import re

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        # [CẬP NHẬT] Thay vì lấy all, ta loại bỏ assigned_telesale để ẩn khỏi giao diện
        exclude = ['assigned_telesale', 'created_at', 'ranking', 'customer_code'] 
        
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên khách hàng'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0xxxxxxxxx'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zalo_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_link': forms.URLInput(attrs={'class': 'form-control'}),
            # 'assigned_telesale': ... -> Đã xóa dòng này để không hiện Select box
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not re.match(r'^0\d{9}$', phone):
                raise forms.ValidationError("Số điện thoại không hợp lệ (Phải là 10 số và bắt đầu bằng số 0).")
        return phone