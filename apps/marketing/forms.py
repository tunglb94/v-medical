from django import forms
from .models import DailyCampaignStat, MarketingTask

# --- FORM CŨ ---
class DailyStatForm(forms.ModelForm):
    class Meta:
        model = DailyCampaignStat
        fields = ['report_date', 'spend_amount', 'comments', 'inboxes', 'leads', 'appointments']
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control fw-bold'}),
            'spend_amount': forms.NumberInput(attrs={'class': 'form-control text-danger fw-bold', 'placeholder': '0'}),
            'comments': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'inboxes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'leads': forms.NumberInput(attrs={'class': 'form-control text-primary fw-bold', 'placeholder': '0'}),
            'appointments': forms.NumberInput(attrs={'class': 'form-control text-success fw-bold', 'placeholder': '0'}),
        }

# --- FORM MỚI: TASK ---
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