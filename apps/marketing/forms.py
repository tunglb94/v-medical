from django import forms
from .models import ContentAd, DailyCampaignStat, MarketingTask

class ContentAdForm(forms.ModelForm):
    class Meta:
        model = ContentAd
        fields = '__all__'

class DailyStatForm(forms.ModelForm):
    class Meta:
        model = DailyCampaignStat
        # Loại trừ revenue_ads và created_at
        exclude = ['revenue_ads', 'created_at'] 
        
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            
            # --- THÊM WIDGET CHO PLATFORM ---
            'platform': forms.Select(attrs={'class': 'form-select form-select-sm fw-bold'}),
            
            'marketer': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'service': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'spend_amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm fw-bold'}),
            
            # --- CÁC CHỈ SỐ MỚI ---
            'impressions': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Lượt hiển thị'}),
            'clicks': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Lượt click'}),
            'views': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Lượt xem video'}),
            
            # --- CÁC CHỈ SỐ CŨ ---
            'comments': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'inboxes': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'leads': forms.NumberInput(attrs={'class': 'form-control form-control-sm fw-bold'}),
            'appointments': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }

class MarketingTaskForm(forms.ModelForm):
    class Meta:
        model = MarketingTask
        fields = '__all__'