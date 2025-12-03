from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone
import json

from .models import MarketingTask, DailyCampaignStat
from apps.sales.models import Service
from apps.authentication.decorators import allowed_users

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def marketing_dashboard(request):
    today = timezone.now().date()
    start_month = today.replace(day=1)
    
    stats = DailyCampaignStat.objects.filter(date__gte=start_month)
    total_spend = stats.aggregate(Sum('spend'))['spend__sum'] or 0
    total_conv = stats.aggregate(Sum('conversions'))['conversions__sum'] or 0
    total_rev = stats.aggregate(Sum('revenue_ads'))['revenue_ads__sum'] or 0
    
    cost_per_conv = (total_spend / total_conv) if total_conv > 0 else 0
    roi = ((total_rev - total_spend) / total_spend * 100) if total_spend > 0 else 0

    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%d/%m') for d in last_7_days]
    chart_spend = []
    chart_rev = []

    for d in last_7_days:
        day_stat = DailyCampaignStat.objects.filter(date=d).first()
        chart_spend.append(int(day_stat.spend) if day_stat else 0)
        chart_rev.append(int(day_stat.revenue_ads) if day_stat else 0)

    context = {
        'total_spend': total_spend,
        'total_conv': total_conv,
        'cost_per_conv': cost_per_conv,
        'roi': roi,
        'chart_labels': chart_labels,
        'chart_spend': chart_spend,
        'chart_rev': chart_rev
    }
    return render(request, 'marketing/dashboard.html', context)

# --- 2. QUẢN LÝ CONTENT & ADS ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR'])
def content_ads_list(request):
    tasks = MarketingTask.objects.all().order_by('-created_at')
    services = Service.objects.filter(is_active=True) # Lấy danh sách dịch vụ

    if request.method == 'POST':
        title = request.POST.get('title')
        platform = request.POST.get('platform')
        status = request.POST.get('status')
        content = request.POST.get('content')
        budget = request.POST.get('budget', 0)
        
        # Nhận dữ liệu mới
        service_id = request.POST.get('service_id')
        start_date = request.POST.get('start_date')
        deadline = request.POST.get('deadline')
        script_link = request.POST.get('script_link')

        if title:
            MarketingTask.objects.create(
                title=title,
                platform=platform,
                status=status,
                content=content,
                budget=budget if budget else 0,
                assigned_to=request.user,
                # Lưu các trường mới
                service_id=service_id if service_id else None,
                start_date=start_date if start_date else None,
                deadline=deadline if deadline else None,
                script_link=script_link
            )
            messages.success(request, "Đã thêm công việc mới!")
            return redirect('content_ads_list')

    context = {
        'tasks': tasks,
        'services': services
    }
    return render(request, 'marketing/content_ads.html', context)

# --- 3. LỊCH MARKETING (WORKSPACE) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR'])
def marketing_workspace(request):
    # Lấy task để hiển thị lên lịch
    tasks = MarketingTask.objects.all()
    
    events = []
    tasks_urgent = []
    today = timezone.now().date()

    for t in tasks:
        # Xử lý dữ liệu cho FullCalendar
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
                evt['end'] = (t.deadline + timedelta(days=1)).strftime('%Y-%m-%d') # FullCalendar exclusive end date
            
            # Màu sắc
            if t.status == 'COMPLETED': evt['color'] = '#1cc88a'
            elif t.status == 'RUNNING': evt['color'] = '#4e73df'
            elif t.status == 'WRITING': evt['color'] = '#f6c23e'
            elif t.status == 'PAUSED': evt['color'] = '#e74a3b'
            else: evt['color'] = '#858796'

            events.append(evt)

        # Xử lý list task gấp bên trái (nếu chưa xong và có deadline)
        if t.status != 'COMPLETED' and t.deadline:
            t.is_overdue = t.deadline < today
            tasks_urgent.append(t)

    context = {
        'events_json': json.dumps(events),
        'tasks_urgent': tasks_urgent
    }
    return render(request, 'marketing/workspace.html', context)