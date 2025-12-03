from django import forms
from .models import ContentAd, DailyCampaignStat, MarketingTask

class ContentAdForm(forms.ModelForm):
    class Meta:
        model = ContentAd
        fields = '__all__'

class DailyStatForm(forms.ModelForm):
    class Meta:
        model = DailyCampaignStat
        fields = '__all__'
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date'}),
        }

class MarketingTaskForm(forms.ModelForm):
    class Meta:
        model = MarketingTask
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }