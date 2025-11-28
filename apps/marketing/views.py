from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.http import JsonResponse # <--- Mới thêm

from .models import DailyCampaignStat, MarketingTask
from .forms import DailyStatForm, MarketingTaskForm
from apps.authentication.decorators import allowed_users

# --- 1. DASHBOARD MARKETING (Code cũ giữ nguyên) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE', 'MARKETING']) # Thêm role MARKETING nếu có
def marketing_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    
    if request.method == 'POST':
        report_date_str = request.POST.get('report_date')
        instance = None
        if report_date_str:
            instance = DailyCampaignStat.objects.filter(report_date=report_date_str).first()
            
        form = DailyStatForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            action = "cập nhật" if instance else "thêm mới"
            messages.success(request, f"Đã {action} báo cáo ngày {report_date_str}")
            return redirect('marketing_dashboard')
        else:
            messages.error(request, f"Lỗi nhập liệu: {form.errors.as_text()}")
    else:
        form = DailyStatForm(initial={'report_date': today})

    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end]).order_by('-report_date')
    
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'), sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'), sum_comments=Sum('comments'), sum_inboxes=Sum('inboxes')
    )
    
    total_spend = totals['sum_spend'] or 0
    total_leads = totals['sum_leads'] or 0
    total_appts = totals['sum_appts'] or 0
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0
    
    chart_dates, chart_cpl, chart_leads, enhanced_stats = [], [], [], []
    
    for stat in stats:
        prev_day = stat.report_date - timedelta(days=1)
        try:
            prev_stat = DailyCampaignStat.objects.get(report_date=prev_day)
            trend_lead = ((stat.leads - prev_stat.leads) / prev_stat.leads) * 100 if prev_stat.leads > 0 else (100 if stat.leads > 0 else 0)
        except DailyCampaignStat.DoesNotExist:
            trend_lead = 0
            
        stat.trend_lead = trend_lead
        enhanced_stats.append(stat)
        chart_dates.insert(0, stat.report_date.strftime('%d/%m'))
        chart_cpl.insert(0, float(stat.cost_per_lead))
        chart_leads.insert(0, stat.leads)

    context = {
        'stats': enhanced_stats, 'form': form, 'totals': totals,
        'avg_cpl': avg_cpl, 'avg_cpa': avg_cpa,
        'chart_dates': chart_dates, 'chart_cpl': chart_cpl, 'chart_leads': chart_leads,
        'date_start': date_start, 'date_end': date_end,
    }
    return render(request, 'marketing/dashboard.html', context)

# --- 2. XÓA BÁO CÁO (Code cũ giữ nguyên) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def delete_report(request, pk):
    report = get_object_or_404(DailyCampaignStat, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, f"Đã xóa báo cáo ngày {report.report_date}")
    return redirect('marketing_dashboard')

# --- 3. MARKETING WORKSPACE (MỚI) ---
@login_required(login_url='/auth/login/')
# Thêm role MARKETING vào đây khi bạn đã tạo role trong Model User
def marketing_workspace(request):
    today = timezone.now().date()
    
    # Lấy danh sách việc cần nhắc nhở (Quá hạn hoặc Đến hạn hôm nay, và chưa xong)
    tasks_urgent = MarketingTask.objects.exclude(status='DONE').filter(
        deadline__lte=today
    ).order_by('deadline')
    
    # Xử lý Form thêm việc nhanh
    if request.method == 'POST':
        form = MarketingTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã tạo công việc mới!")
            return redirect('marketing_workspace')
        else:
            messages.error(request, "Lỗi nhập liệu, vui lòng kiểm tra lại.")
    else:
        form = MarketingTaskForm(initial={'start_date': today, 'deadline': today})

    context = {
        'form': form,
        'tasks_urgent': tasks_urgent,
        'today': today
    }
    return render(request, 'marketing/workspace.html', context)

# --- 4. API LẤY TASK CHO LỊCH (MỚI) ---
@login_required(login_url='/auth/login/')
def get_marketing_tasks_api(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Lọc task theo khung thời gian hiển thị trên lịch
    # (Lấy task có ngày bắt đầu HOẶC deadline nằm trong khoảng này)
    # Ở đây đơn giản hóa lấy theo start_date
    tasks = MarketingTask.objects.filter(start_date__range=[start, end])
    
    events = []
    for task in tasks:
        # Màu sắc theo loại công việc
        color = '#3788d8' # Mặc định
        if task.category == 'DESIGN': color = '#e67e22' # Cam
        elif task.category == 'CONTENT': color = '#2ecc71' # Xanh lá
        elif task.category == 'VIDEO': color = '#e74c3c' # Đỏ
        elif task.category == 'ADS': color = '#9b59b6' # Tím
        
        # Nếu xong rồi thì màu xám
        if task.status == 'DONE': color = '#95a5a6'
        
        events.append({
            'id': task.id,
            'title': f"{task.get_category_display()}: {task.title}",
            'start': task.start_date.isoformat(),
            'end': task.deadline.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'pic': task.pic.username if task.pic else "Chưa gán",
                'status': task.get_status_display(),
                'statusCode': task.status,
                'note': task.note
            }
        })
        
    return JsonResponse(events, safe=False)