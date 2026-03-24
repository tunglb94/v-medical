from django import forms
from .models import Customer, Fanpage
import re

class CustomerForm(forms.ModelForm):
    # [CẬP NHẬT] Sử dụng trường ManyToMany cho Fanpages
    fanpages = forms.ModelMultipleChoiceField(
        queryset=Fanpage.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Các Fanpage Nguồn"
    )

    class Meta:
        model = Customer
        # [CẬP NHẬT] Loại bỏ fanpage (cũ), giữ nguyên các trường exclude khác
        exclude = ['assigned_telesale', 'created_at', 'ranking', 'customer_code', 'fanpage'] 
        
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên khách hàng'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0xxxxxxxxx'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-select', 'id': 'id_source'}),
            'skin_condition': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'note_telesale': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not re.match(r'^0\d{9}$', phone):
                raise forms.ValidationError("Số điện thoại không hợp lệ (Phải là 10 số và bắt đầu bằng số 0).")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source')
        fanpages = cleaned_data.get('fanpages')

        # [LOGIC MỚI] Nếu nguồn là Facebook Ads, bắt buộc phải chọn ít nhất 1 Fanpage
        if source == 'FACEBOOK' and not fanpages:
            self.add_error('fanpages', "Bắt buộc phải chọn Fanpage khi nguồn là Facebook Ads.")
        
        return cleaned_data