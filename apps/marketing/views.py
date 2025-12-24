from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
import json

from .models import MarketingTask, DailyCampaignStat, ContentAd, TaskFeedback
from apps.sales.models import Service
from apps.authentication.decorators import allowed_users
from .forms import DailyStatForm, MarketingTaskForm, ContentAdForm
from apps.authentication.models import User 

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'TELESALE', 'CONTENT', 'EDITOR', 'DESIGNER'])
def marketing_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    marketer_query = request.GET.get('marketer', '')
    service_query = request.GET.get('service', '')
    
    # --- THÊM BIẾN LỌC THEO PLATFORM ---
    platform_query = request.GET.get('platform', '') 
    
    # Xử lý Form thêm/sửa báo cáo
    if request.method == 'POST':
        stat_id = request.POST.get('stat_id')
        instance = get_object_or_404(DailyCampaignStat, id=stat_id) if stat_id else None
        form = DailyStatForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã lưu dữ liệu báo cáo!")
            return redirect('marketing_dashboard')
        else:
            messages.error(request, f"Lỗi: {form.errors}")
    else:
        form = DailyStatForm(initial={'report_date': today})

    # Lọc dữ liệu
    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end])
    if marketer_query:
        stats = stats.filter(marketer__icontains=marketer_query)
    if service_query:
        stats = stats.filter(service__icontains=service_query)
        
    # --- ÁP DỤNG LỌC PLATFORM ---
    if platform_query:
        stats = stats.filter(platform=platform_query)
        
    # Sắp xếp theo ngày và platform
    stats = stats.order_by('-report_date', 'platform', 'marketer')
    
    # Tính tổng KPI (Cập nhật thêm fields mới)
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'), 
        sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'), 
        sum_comments=Sum('comments'), 
        sum_inboxes=Sum('inboxes'),
        # --- Tổng mới ---
        sum_impressions=Sum('impressions'),
        sum_clicks=Sum('clicks'),
        sum_views=Sum('views')
    )
    
    for key in totals:
        if totals[key] is None: totals[key] = 0

    total_spend = totals['sum_spend']
    total_leads = totals['sum_leads']
    total_appts = totals['sum_appts']
    total_clicks = totals['sum_clicks']
    total_impr = totals['sum_impressions']
    
    # --- TÍNH CÁC CHỈ SỐ TRUNG BÌNH ---
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0
    avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    avg_ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0
    
    # Chart Data
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
    
    # Lấy danh sách Platform để hiển thị dropdown lọc
    platform_choices = DailyCampaignStat.Platform.choices

    context = {
        'stats': stats, 'form': form, 'totals': totals,
        'avg_cpl': avg_cpl, 'avg_cpa': avg_cpa,
        'avg_cpc': avg_cpc, 'avg_ctr': avg_ctr, # Truyền thêm xuống template
        'chart_dates': chart_dates, 'chart_cpl': chart_cpl, 'chart_leads': chart_leads,
        'date_start': date_start, 'date_end': date_end,
        'marketer_query': marketer_query, 'service_query': service_query,
        'platform_query': platform_query, # Giữ trạng thái lọc
        'platform_choices': platform_choices # Danh sách options lọc
    }
    return render(request, 'marketing/dashboard.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def delete_report(request, pk):
    get_object_or_404(DailyCampaignStat, pk=pk).delete()
    messages.success(request, "Đã xóa báo cáo.")
    return redirect('marketing_dashboard')

# --- 2. QUẢN LÝ CONTENT ADS & LỊCH ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER'])
def content_ads_list(request):
    # Sửa lỗi: Bỏ filter(is_active=True) vì model Service không có trường này
    services = Service.objects.all()
    staffs = User.objects.filter(is_active=True).exclude(is_superuser=True)
    
    tasks = MarketingTask.objects.all().select_related('pic_content', 'pic_design', 'pic_ads', 'created_by', 'service')

    keyword = request.GET.get('keyword', '')
    if keyword:
        tasks = tasks.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

    service_id = request.GET.get('service_id', '')
    if service_id:
        tasks = tasks.filter(service_id=service_id)

    platform = request.GET.get('platform', '')
    if platform:
        tasks = tasks.filter(platform=platform)

    status = request.GET.get('status', '')
    if status:
        tasks = tasks.filter(status=status)
        
    pic_id = request.GET.get('pic_id', '')
    if pic_id:
        tasks = tasks.filter(
            Q(pic_content_id=pic_id) | 
            Q(pic_design_id=pic_id) | 
            Q(pic_ads_id=pic_id)
        )

    tasks = tasks.order_by('-created_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            MarketingTask.objects.create(
                title=title,
                platform=request.POST.get('platform'),
                status=request.POST.get('status'),
                content=request.POST.get('content'),
                service_id=request.POST.get('service_id') or None,
                start_date=request.POST.get('start_date') or None,
                deadline=request.POST.get('deadline') or None,
                pic_content_id=request.POST.get('pic_content') or None,
                pic_design_id=request.POST.get('pic_design') or None,
                pic_ads_id=request.POST.get('pic_ads') or None,
                link_source=request.POST.get('link_source'),
                link_thumb=request.POST.get('link_thumb'),
                link_final=request.POST.get('link_final'),
                created_by=request.user 
            )
            messages.success(request, "Đã thêm công việc mới!")
            return redirect('content_ads_list')

    context = {
        'tasks': tasks, 
        'services': services, 
        'staffs': staffs,
        'keyword': keyword,
        'selected_service': int(service_id) if service_id else '',
        'selected_platform': platform,
        'selected_status': status,
        'selected_pic': int(pic_id) if pic_id else ''
    }
    return render(request, 'marketing/content_ads.html', context)

# --- 3. SỬA TASK & LƯU FEEDBACK ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER'])
def content_ads_edit(request, pk):
    task = get_object_or_404(MarketingTask, pk=pk)
    
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.service_id = request.POST.get('service_id') or None
        task.platform = request.POST.get('platform')
        task.status = request.POST.get('status')
        
        start_date = request.POST.get('start_date')
        task.start_date = start_date if start_date else None
        
        deadline = request.POST.get('deadline')
        task.deadline = deadline if deadline else None
        
        task.pic_content_id = request.POST.get('pic_content') or None
        task.pic_design_id = request.POST.get('pic_design') or None
        task.pic_ads_id = request.POST.get('pic_ads') or None
        
        task.link_source = request.POST.get('link_source')
        task.link_thumb = request.POST.get('link_thumb')
        task.link_final = request.POST.get('link_final')
        task.content = request.POST.get('content')
        
        task.save()

        # --- LƯU FEEDBACK ---
        new_feedback = request.POST.get('new_feedback')
        if new_feedback and new_feedback.strip():
            TaskFeedback.objects.create(
                task=task,
                user=request.user,
                content=new_feedback.strip()
            )
        
        messages.success(request, f"Đã cập nhật công việc: {task.title}")
        
    return redirect('content_ads_list')

# --- 4. API LẤY LỊCH SỬ FEEDBACK ---
@login_required
def get_task_feedback_api(request, task_id):
    feedbacks = TaskFeedback.objects.filter(task_id=task_id).select_related('user').order_by('-created_at')
    
    data = []
    for fb in feedbacks:
        time_str = fb.created_at.strftime("%H:%M %d/%m")
        user_name = fb.user.last_name + " " + fb.user.first_name
        if not user_name.strip():
            user_name = fb.user.username

        data.append({
            'user': user_name,
            'role': fb.user.get_role_display(),
            'avatar': fb.user.username[0].upper(),
            'content': fb.content,
            'time': time_str,
            'is_me': fb.user == request.user
        })
    
    return JsonResponse(data, safe=False)

@login_required(login_url='/auth/login/')
def content_ads_delete(request, pk):
    task = get_object_or_404(MarketingTask, pk=pk)
    
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        task.delete()
        messages.success(request, "Đã xóa công việc.")
    else:
        messages.error(request, "Bạn không có quyền xóa công việc này (Chỉ Admin mới có quyền).")
        
    return redirect('content_ads_list')

@login_required(login_url='/auth/login/')
def marketing_workspace(request):
    tasks = MarketingTask.objects.all()
    events = []
    tasks_urgent = []
    today = timezone.now().date()

    for t in tasks:
        if t.start_date:
            pic_name = t.pic_content.last_name if t.pic_content else "--"
            evt = {
                'title': f"[{t.platform}] {t.title}",
                'start': t.start_date.strftime('%Y-%m-%d'),
                'extendedProps': {'pic': pic_name, 'status': t.get_status_display(), 'note': t.content}
            }
            if t.deadline: evt['end'] = (t.deadline + timedelta(days=1)).strftime('%Y-%m-%d')
            
            if t.status == 'COMPLETED': evt['color'] = '#1cc88a'
            elif t.status == 'RUNNING': evt['color'] = '#4e73df'
            elif t.status == 'WRITING': evt['color'] = '#f6c23e'
            else: evt['color'] = '#858796'
            events.append(evt)

        if t.status != 'COMPLETED' and t.deadline:
            t.is_overdue = t.deadline < today
            tasks_urgent.append(t)

    return render(request, 'marketing/workspace.html', {'events_json': json.dumps(events), 'tasks_urgent': tasks_urgent})

@login_required(login_url='/auth/login/')
def get_marketing_tasks_api(request):
    start = request.GET.get('start', '').split('T')[0]
    end = request.GET.get('end', '').split('T')[0]
    tasks = MarketingTask.objects.filter(start_date__range=[start, end])
    return JsonResponse([], safe=False)