from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.http import JsonResponse

from .models import DailyCampaignStat, MarketingTask
from .forms import DailyStatForm, MarketingTaskForm
from apps.authentication.decorators import allowed_users

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE', 'MARKETING'])
def marketing_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Lấy tham số lọc
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    marketer_query = request.GET.get('marketer', '')
    service_query = request.GET.get('service', '')
    
    # XỬ LÝ LƯU/SỬA
    if request.method == 'POST':
        # Nếu có ID gửi lên -> là Sửa
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

    # LỌC DỮ LIỆU
    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end])
    
    if marketer_query:
        stats = stats.filter(marketer__icontains=marketer_query)
    if service_query:
        stats = stats.filter(service__icontains=service_query)
        
    stats = stats.order_by('-report_date', 'marketer')
    
    # TÍNH TỔNG KPI
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'), sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'), sum_comments=Sum('comments'), sum_inboxes=Sum('inboxes')
    )
    
    total_spend = totals['sum_spend'] or 0
    total_leads = totals['sum_leads'] or 0
    total_appts = totals['sum_appts'] or 0
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0
    
    # CHUẨN BỊ DỮ LIỆU BIỂU ĐỒ (Gom nhóm theo ngày)
    # Vì có thể có nhiều dòng trong 1 ngày (nhiều nhân viên), cần sum lại để vẽ biểu đồ
    chart_data_qs = stats.values('report_date').annotate(
        daily_leads=Sum('leads'),
        daily_spend=Sum('spend_amount')
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
        # Giữ lại giá trị lọc
        'date_start': date_start, 'date_end': date_end,
        'marketer_query': marketer_query, 'service_query': service_query
    }
    return render(request, 'marketing/dashboard.html', context)

# --- 2. XÓA BÁO CÁO ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def delete_report(request, pk):
    report = get_object_or_404(DailyCampaignStat, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, "Đã xóa dòng báo cáo.")
    return redirect('marketing_dashboard')

# --- 3. WORKSPACE & API (GIỮ NGUYÊN) ---
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