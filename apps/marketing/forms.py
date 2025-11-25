from django import forms
from .models import DailyCampaignStat
from django.utils import timezone

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