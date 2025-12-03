from django import forms
from .models import Customer
import re # <--- Import thư viện Regex

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên khách hàng'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0xxxxxxxxx'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zalo_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_link': forms.URLInput(attrs={'class': 'form-control'}),
            'assigned_telesale': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Regex: Bắt đầu bằng 0, theo sau là 9 chữ số (Tổng 10 số)
        if phone:
            # Xóa khoảng trắng nếu có
            phone = phone.strip()
            if not re.match(r'^0\d{9}$', phone):
                raise forms.ValidationError("Số điện thoại không hợp lệ (Phải là 10 số và bắt đầu bằng số 0).")
        return phone