from django import forms
from .models import DailyCampaignStat, MarketingTask, ContentAd

# --- 1. FORM BÁO CÁO NGÀY ---
class DailyStatForm(forms.ModelForm):
    class Meta:
        model = DailyCampaignStat
        fields = ['report_date', 'marketer', 'service', 'spend_amount', 'comments', 'inboxes', 'leads', 'appointments']
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control fw-bold'}),
            'marketer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên người chạy...'}),
            'service': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên dịch vụ...'}),
            'spend_amount': forms.NumberInput(attrs={'class': 'form-control text-danger fw-bold', 'placeholder': '0'}),
            'comments': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'inboxes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'leads': forms.NumberInput(attrs={'class': 'form-control text-primary fw-bold', 'placeholder': '0'}),
            'appointments': forms.NumberInput(attrs={'class': 'form-control text-success fw-bold', 'placeholder': '0'}),
        }

# --- 2. FORM CÔNG VIỆC ---
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

# --- 3. FORM CONTENT ADS (MỚI) ---
class ContentAdForm(forms.ModelForm):
    class Meta:
        model = ContentAd
        fields = ['title', 'content_creator', 'editor', 'marketer', 'ad_headline', 'post_content', 'link_video', 'link_thumb', 'result_note']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Video Trị Mụn T11.01...'}),
            'content_creator': forms.Select(attrs={'class': 'form-select'}),
            'editor': forms.Select(attrs={'class': 'form-select'}),
            'marketer': forms.Select(attrs={'class': 'form-select'}),
            'ad_headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tiêu đề giật tít...'}),
            'post_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Nội dung bài viết...'}),
            'link_video': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'link_thumb': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'result_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Kết quả sơ bộ (CPM, Mess...)'}),
        }