from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'age', 'city', 'address', 'source', 'skin_condition', 'note_telesale']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tuổi'}),
            # Datalist tỉnh thành dùng lại ID của HTML
            'city': forms.TextInput(attrs={'class': 'form-control', 'list': 'provinceOptions', 'placeholder': 'Tỉnh/Thành phố'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ chi tiết'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'skin_condition': forms.Select(attrs={'class': 'form-select'}),
            'note_telesale': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }