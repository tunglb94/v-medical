from django import forms
from .models import Customer, Fanpage
import re
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomerForm(forms.ModelForm):
    # [CẬP NHẬT] Sử dụng MultipleChoiceField lấy data cứng giống hệt bên Telesale
    fanpages = forms.MultipleChoiceField(
        choices=Customer.FanpageChoices.choices,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input me-2 cursor-pointer'}),
        required=False,
        label="Các Fanpage Nguồn"
    )

    class Meta:
        model = Customer
        # [CẬP NHẬT] Đã bỏ 'assigned_telesale' khỏi exclude để hiển thị ô chọn
        exclude = ['created_at', 'ranking', 'customer_code', 'fanpage'] 
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên khách hàng'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0xxxxxxxxx'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-select', 'id': 'id_source'}),
            'skin_condition': forms.Select(attrs={'class': 'form-select'}),
            # [THÊM MỚI] Widget cho ô chọn Telesale
            'assigned_telesale': forms.Select(attrs={'class': 'form-select'}),
            'note_telesale': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chỉ hiển thị các user có role là TELESALE trong danh sách chọn
        if 'assigned_telesale' in self.fields:
            self.fields['assigned_telesale'].queryset = User.objects.filter(role='TELESALE', is_active=True)
            self.fields['assigned_telesale'].label = "Nhân viên phụ trách"
            self.fields['assigned_telesale'].empty_label = "-- Để hệ thống tự chia --"
            self.fields['assigned_telesale'].required = False

        # [QUAN TRỌNG] Khi mở Modal Sửa, tự động check lại các Fanpage mà khách này đã liên kết
        if self.instance and self.instance.pk:
            self.fields['fanpages'].initial = list(self.instance.fanpages.values_list('code', flat=True))

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

    def save(self, commit=True):
        # Lưu Customer trước
        instance = super().save(commit=False)
        if commit:
            instance.save()
            
            # [LOGIC TỰ ĐỘNG ĐỒNG BỘ M2M] 
            # Lấy list các code do user tick chọn
            selected_codes = self.cleaned_data.get('fanpages', [])
            fanpage_objs = []
            choice_dict = dict(Customer.FanpageChoices.choices)
            
            for code in selected_codes:
                name = choice_dict.get(code, code)
                # Tự động tạo bản ghi Fanpage trong DB nếu chưa có -> Tránh lỗi trống data
                fp_obj, _ = Fanpage.objects.get_or_create(code=code, defaults={'name': name})
                fanpage_objs.append(fp_obj)
                
            # Set dữ liệu vào field fanpages
            instance.fanpages.set(fanpage_objs)
            
        return instance