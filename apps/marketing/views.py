from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg

from .models import DailyCampaignStat
from .forms import DailyStatForm
from apps.authentication.decorators import allowed_users

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE']) # Cho phép Admin và Tele (hoặc Marketing nếu có)
def marketing_dashboard(request):
    # 1. XỬ LÝ LỌC NGÀY
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    
    # 2. XỬ LÝ FORM NHẬP LIỆU (POST)
    if request.method == 'POST':
        form = DailyStatForm(request.POST)
        if form.is_valid():
            # Kiểm tra xem ngày này đã nhập chưa, nếu có thì update
            date = form.cleaned_data['report_date']
            obj, created = DailyCampaignStat.objects.update_or_create(
                report_date=date,
                defaults=form.cleaned_data
            )
            messages.success(request, f"Đã lưu báo cáo marketing ngày {date}")
            return redirect('marketing_dashboard')
    else:
        form = DailyStatForm(initial={'report_date': today})

    # 3. LẤY DỮ LIỆU BÁO CÁO
    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end]).order_by('-report_date')
    
    # Tính tổng KPI trong kỳ
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'),
        sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'),
        sum_comments=Sum('comments'),
        sum_inboxes=Sum('inboxes')
    )
    
    # Tính chỉ số hiệu quả trung bình
    total_spend = totals['sum_spend'] or 0
    total_leads = totals['sum_leads'] or 0
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    
    # 4. CHUẨN BỊ DỮ LIỆU BIỂU ĐỒ
    chart_dates = []
    chart_cpl = []
    chart_leads = []
    
    # Xử lý logic so sánh tăng giảm (Trend)
    enhanced_stats = []
    for i, stat in enumerate(stats):
        # Tìm ngày hôm trước để so sánh
        prev_day = stat.report_date - timedelta(days=1)
        try:
            prev_stat = DailyCampaignStat.objects.get(report_date=prev_day)
            # Tính % tăng giảm Leads
            if prev_stat.leads > 0:
                trend_lead = ((stat.leads - prev_stat.leads) / prev_stat.leads) * 100
            else:
                trend_lead = 100 if stat.leads > 0 else 0
        except DailyCampaignStat.DoesNotExist:
            trend_lead = 0
            
        # Gán thêm thuộc tính trend vào object để hiển thị template
        stat.trend_lead = trend_lead
        enhanced_stats.append(stat)
        
        # Data biểu đồ (Đảo ngược lại cho đúng chiều thời gian nếu cần, hoặc để ChartJS xử lý)
        chart_dates.insert(0, stat.report_date.strftime('%d/%m'))
        chart_cpl.insert(0, float(stat.cost_per_lead))
        chart_leads.insert(0, stat.leads)

    context = {
        'stats': enhanced_stats,
        'form': form,
        'totals': totals,
        'avg_cpl': avg_cpl,
        
        # Chart Data
        'chart_dates': chart_dates,
        'chart_cpl': chart_cpl,
        'chart_leads': chart_leads,
        
        'date_start': date_start,
        'date_end': date_end,
    }
    return render(request, 'marketing/dashboard.html', context)