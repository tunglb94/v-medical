from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
import json

# Import đầy đủ các model để tránh lỗi
from .models import MarketingTask, DailyCampaignStat, ContentAd
from apps.sales.models import Service
from apps.authentication.decorators import allowed_users
from .forms import DailyStatForm # Đảm bảo file forms.py đã có class này

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def marketing_dashboard(request):
    today = timezone.now().date()
    start_month = today.replace(day=1)
    
    # Xử lý form thêm báo cáo ngày (DailyStatForm)
    if request.method == 'POST':
        stat_id = request.POST.get('stat_id')
        instance = None
        if stat_id:
            instance = get_object_or_404(DailyCampaignStat, id=stat_id)
            
        form = DailyStatForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã lưu báo cáo Ads!")
            return redirect('marketing_dashboard')
        else:
            messages.error(request, f"Lỗi: {form.errors}")
    
    # Thống kê
    stats = DailyCampaignStat.objects.filter(date__gte=start_month).order_by('-date')
    total_spend = stats.aggregate(Sum('spend_amount'))['spend_amount__sum'] or 0
    total_conv = stats.aggregate(Sum('conversions'))['conversions__sum'] or 0
    total_rev = stats.aggregate(Sum('revenue_ads'))['revenue_ads__sum'] or 0
    
    cost_per_conv = (total_spend / total_conv) if total_conv > 0 else 0
    roi = ((total_rev - total_spend) / total_spend * 100) if total_spend > 0 else 0

    # Biểu đồ 7 ngày
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%d/%m') for d in last_7_days]
    chart_spend = []
    chart_rev = []

    for d in last_7_days:
        day_stat = DailyCampaignStat.objects.filter(date=d).first()
        chart_spend.append(int(day_stat.spend_amount) if day_stat else 0)
        chart_rev.append(int(day_stat.revenue_ads) if day_stat else 0)

    context = {
        'stats': stats,
        'total_spend': total_spend,
        'total_conv': total_conv,
        'cost_per_conv': cost_per_conv,
        'roi': roi,
        'chart_labels': chart_labels,
        'chart_spend': chart_spend,
        'chart_rev': chart_rev
    }
    return render(request, 'marketing/dashboard.html', context)

# --- [KHÔI PHỤC] Hàm xóa báo cáo ngày ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def delete_report(request, pk):
    report = get_object_or_404(DailyCampaignStat, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, "Đã xóa dòng báo cáo.")
    return redirect('marketing_dashboard')

# --- 2. QUẢN LÝ CONTENT & ADS (LOGIC MỚI: DÙNG MARKETING TASK) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR'])
def content_ads_list(request):
    # Sử dụng MarketingTask để quản lý vì có deadline, status, calendar support
    tasks = MarketingTask.objects.all().order_by('-created_at')
    services = Service.objects.filter(is_active=True)

    if request.method == 'POST':
        # Nhận dữ liệu từ Form Modal
        title = request.POST.get('title')
        if title:
            MarketingTask.objects.create(
                title=title,
                platform=request.POST.get('platform'),
                status=request.POST.get('status'),
                content=request.POST.get('content'),
                budget=request.POST.get('budget') or 0,
                assigned_to=request.user,
                # Các trường mới bạn yêu cầu
                service_id=request.POST.get('service_id') or None,
                start_date=request.POST.get('start_date') or None,
                deadline=request.POST.get('deadline') or None,
                script_link=request.POST.get('script_link')
            )
            messages.success(request, "Đã thêm công việc/content mới!")
            return redirect('content_ads_list')

    context = {
        'tasks': tasks,
        'services': services
    }
    return render(request, 'marketing/content_ads.html', context)

# --- [KHÔI PHỤC] Hàm xóa Content/Ads ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT'])
def content_ads_delete(request, pk):
    # Xóa task
    task = get_object_or_404(MarketingTask, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Đã xóa công việc.")
    return redirect('content_ads_list')

# --- 3. LỊCH MARKETING (WORKSPACE) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR'])
def marketing_workspace(request):
    tasks = MarketingTask.objects.all()
    events = []
    tasks_urgent = []
    today = timezone.now().date()

    for t in tasks:
        # Chỉ hiện lên lịch nếu có ngày bắt đầu
        if t.start_date:
            evt = {
                'title': f"[{t.platform}] {t.title}",
                'start': t.start_date.strftime('%Y-%m-%d'),
                'extendedProps': {
                    'pic': t.assigned_to.last_name if t.assigned_to else "Chưa giao",
                    'status': t.get_status_display(),
                    'note': t.content
                }
            }
            if t.deadline:
                evt['end'] = (t.deadline + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Màu sắc
            if t.status == 'COMPLETED': evt['color'] = '#1cc88a'
            elif t.status == 'RUNNING': evt['color'] = '#4e73df'
            elif t.status == 'WRITING': evt['color'] = '#f6c23e'
            elif t.status == 'PAUSED': evt['color'] = '#e74a3b'
            else: evt['color'] = '#858796'

            events.append(evt)

        # List việc gấp
        if t.status != 'COMPLETED' and t.deadline:
            t.is_overdue = t.deadline < today
            tasks_urgent.append(t)

    context = {
        'events_json': json.dumps(events),
        'tasks_urgent': tasks_urgent
    }
    return render(request, 'marketing/workspace.html', context)

# --- API CHO LỊCH (ĐÃ SỬA DATE FORMAT) ---
@login_required(login_url='/auth/login/')
def get_marketing_tasks_api(request):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    
    # Fix lỗi format ISO (2025-11-30T...)
    if start_str and 'T' in start_str: start_str = start_str.split('T')[0]
    if end_str and 'T' in end_str: end_str = end_str.split('T')[0]

    tasks = MarketingTask.objects.filter(start_date__range=[start_str, end_str])
    events = []
    for task in tasks:
        events.append({
            'title': f"{task.platform}: {task.title}",
            'start': task.start_date.strftime('%Y-%m-%d') if task.start_date else '',
            'end': task.deadline.strftime('%Y-%m-%d') if task.deadline else '',
        })
    return JsonResponse(events, safe=False)