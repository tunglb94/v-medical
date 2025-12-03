from django import forms
from .models import ContentAd, DailyCampaignStat, MarketingTask

class ContentAdForm(forms.ModelForm):
    class Meta:
        model = ContentAd
        fields = '__all__'

class DailyStatForm(forms.ModelForm):
    class Meta:
        model = DailyCampaignStat
        # SỬA Ở ĐÂY: Thay vì lấy tất cả, ta loại trừ revenue_ads và created_at
        exclude = ['revenue_ads', 'created_at'] 
        
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'marketer': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'service': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'spend_amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm fw-bold'}),
            'comments': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'inboxes': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'leads': forms.NumberInput(attrs={'class': 'form-control form-control-sm fw-bold'}),
            'appointments': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }

class MarketingTaskForm(forms.ModelForm):
    class Meta:
        model = MarketingTask
        fields = '__all__'