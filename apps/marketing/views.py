from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.conf import settings 

# Import thư viện AI
import google.generativeai as genai

from .models import DailyCampaignStat, MarketingTask, ContentAd
from .forms import DailyStatForm, MarketingTaskForm, ContentAdForm
from apps.authentication.decorators import allowed_users

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE', 'MARKETING'])
def marketing_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    marketer_query = request.GET.get('marketer', '')
    service_query = request.GET.get('service', '')
    
    if request.method == 'POST':
        stat_id = request.POST.get('stat_id')
        instance = None
        if stat_id:
            instance = get_object_or_404(DailyCampaignStat, id=stat_id)
            
        form = DailyStatForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            action = "cập nhật" if instance else "thêm mới"
            messages.success(request, f"Đã {action} báo cáo thành công!")
            return redirect('marketing_dashboard')
        else:
            messages.error(request, f"Lỗi nhập liệu: {form.errors.as_text()}")
    else:
        form = DailyStatForm(initial={'report_date': today})

    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end])
    if marketer_query: stats = stats.filter(marketer__icontains=marketer_query)
    if service_query: stats = stats.filter(service__icontains=service_query)
    stats = stats.order_by('-report_date', 'marketer')
    
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'), sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'), sum_comments=Sum('comments'), sum_inboxes=Sum('inboxes')
    )
    
    total_spend = totals['sum_spend'] or 0
    total_leads = totals['sum_leads'] or 0
    total_appts = totals['sum_appts'] or 0
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0
    
    chart_data_qs = stats.values('report_date').annotate(
        daily_leads=Sum('leads'), daily_spend=Sum('spend_amount')
    ).order_by('report_date')

    chart_dates = []
    chart_cpl = []
    chart_leads = []
    for item in chart_data_qs:
        d_leads = item['daily_leads'] or 0
        d_spend = item['daily_spend'] or 0
        d_cpl = (d_spend / d_leads) if d_leads > 0 else 0
        chart_dates.append(item['report_date'].strftime('%d/%m'))
        chart_leads.append(d_leads)
        chart_cpl.append(float(d_cpl))

    context = {
        'stats': stats, 'form': form, 'totals': totals,
        'avg_cpl': avg_cpl, 'avg_cpa': avg_cpa,
        'chart_dates': chart_dates, 'chart_cpl': chart_cpl, 'chart_leads': chart_leads,
        'date_start': date_start, 'date_end': date_end,
        'marketer_query': marketer_query, 'service_query': service_query
    }
    return render(request, 'marketing/dashboard.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE', 'MARKETING'])
def delete_report(request, pk):
    report = get_object_or_404(DailyCampaignStat, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, "Đã xóa dòng báo cáo.")
    return redirect('marketing_dashboard')

# --- 2. MARKETING WORKSPACE ---
@login_required(login_url='/auth/login/')
def marketing_workspace(request):
    today = timezone.now().date()
    tasks_urgent = MarketingTask.objects.exclude(status='DONE').filter(deadline__lte=today).order_by('deadline')
    
    if request.method == 'POST':
        form = MarketingTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã tạo công việc mới!")
            return redirect('marketing_workspace')
    else:
        form = MarketingTaskForm(initial={'start_date': today, 'deadline': today})

    return render(request, 'marketing/workspace.html', {'form': form, 'tasks_urgent': tasks_urgent, 'today': today})

@login_required(login_url='/auth/login/')
def get_marketing_tasks_api(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    tasks = MarketingTask.objects.filter(start_date__range=[start, end])
    events = []
    for task in tasks:
        color = '#3788d8'
        if task.category == 'DESIGN': color = '#e67e22'
        elif task.category == 'CONTENT': color = '#2ecc71'
        elif task.category == 'VIDEO': color = '#e74c3c'
        elif task.category == 'ADS': color = '#9b59b6'
        if task.status == 'DONE': color = '#95a5a6'
        events.append({
            'id': task.id,
            'title': f"{task.get_category_display()}: {task.title}",
            'start': task.start_date.isoformat(),
            'end': task.deadline.isoformat(),
            'backgroundColor': color, 'borderColor': color,
            'extendedProps': {'pic': task.pic.username if task.pic else "--", 'status': task.get_status_display(), 'note': task.note}
        })
    return JsonResponse(events, safe=False)

# --- 3. QUẢN LÝ CONTENT ADS ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE', 'MARKETING', 'CONTENT', 'EDITOR']) 
def content_ads_list(request):
    if request.method == 'POST':
        ad_id = request.POST.get('ad_id')
        instance = None
        if ad_id:
            instance = get_object_or_404(ContentAd, id=ad_id)
        
        form = ContentAdForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            action = "cập nhật" if instance else "thêm mới"
            messages.success(request, f"Đã {action} bài Content Ads!")
            return redirect('content_ads_list')
        else:
            messages.error(request, f"Lỗi: {form.errors.as_text()}")
    else:
        form = ContentAdForm()

    ads = ContentAd.objects.all().order_by('-created_at')
    search_query = request.GET.get('q', '')
    
    if search_query:
        ads = ads.filter(
            Q(title__icontains=search_query) | 
            Q(ad_headline__icontains=search_query) |
            Q(content_creator__username__icontains=search_query)
        )

    return render(request, 'marketing/content_ads.html', {'ads': ads, 'form': form, 'search_query': search_query})

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def content_ads_delete(request, pk):
    ad = get_object_or_404(ContentAd, pk=pk)
    if request.method == 'POST':
        ad.delete()
        messages.success(request, "Đã xóa bài Content Ads.")
    return redirect('content_ads_list')

# --- 4. API GỌI GEMINI (ĐÃ SỬA LỖI MODEL) ---
@login_required(login_url='/auth/login/')
def generate_ad_content_api(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        if not prompt:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập yêu cầu.'})
        
        try:
            # Cấu hình Gemini
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if not api_key:
                return JsonResponse({'success': False, 'error': 'Chưa cấu hình GEMINI_API_KEY trong settings.py'})

            genai.configure(api_key=api_key)
            
            # --- SỬ DỤNG MODEL GEMINI-PRO (ỔN ĐỊNH HƠN) ---
            model = genai.GenerativeModel('gemini-pro') 
            
            full_prompt = f"""
            Bạn là một chuyên gia Copywriter cho Thẩm mỹ viện. Hãy viết một bài quảng cáo Facebook hấp dẫn dựa trên yêu cầu sau:
            "{prompt}"
            
            Yêu cầu:
            - Có tiêu đề giật tít (Headline).
            - Dùng icon sinh động.
            - Chia đoạn rõ ràng, dễ đọc.
            - Có lời kêu gọi hành động (CTA) cuối bài.
            - Giọng văn: Thân thiện, chuyên nghiệp, đánh trúng nỗi đau khách hàng.
            """
            
            response = model.generate_content(full_prompt)
            return JsonResponse({'success': True, 'content': response.text})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})