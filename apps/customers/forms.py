from django import forms
from .models import Customer, Fanpage
import re

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
        # Loại bỏ fanpage (cũ), giữ nguyên các trường exclude khác
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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