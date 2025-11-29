from django import forms
from .models import DailyCampaignStat, MarketingTask

class DailyStatForm(forms.ModelForm):
    class Meta:
        model = DailyCampaignStat
        fields = ['report_date', 'marketer', 'service', 'spend_amount', 'comments', 'inboxes', 'leads', 'appointments']
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control fw-bold'}),
            # Nhập text tự do
            'marketer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên người chạy...'}),
            'service': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên dịch vụ...'}),
            
            'spend_amount': forms.NumberInput(attrs={'class': 'form-control text-danger fw-bold', 'placeholder': '0'}),
            'comments': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'inboxes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'leads': forms.NumberInput(attrs={'class': 'form-control text-primary fw-bold', 'placeholder': '0'}),
            'appointments': forms.NumberInput(attrs={'class': 'form-control text-success fw-bold', 'placeholder': '0'}),
        }

class MarketingTaskForm(forms.ModelForm):
    class Meta:
        model = MarketingTask
        fields = ['title', 'category', 'pic', 'start_date', 'deadline', 'status', 'note']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tiêu đề công việc...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'pic': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Chi tiết yêu cầu...'}),
        }