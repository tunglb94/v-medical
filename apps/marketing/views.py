from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from .models import DailyCampaignStat
from .forms import DailyStatForm
from apps.authentication.decorators import allowed_users

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE'])
def marketing_dashboard(request):
    # A. XỬ LÝ LỌC NGÀY
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    
    # B. XỬ LÝ FORM NHẬP LIỆU (ĐÃ SỬA LỖI LOGIC UPDATE)
    if request.method == 'POST':
        # Lấy ngày từ form gửi lên để kiểm tra xem đã tồn tại chưa
        report_date_str = request.POST.get('report_date')
        
        instance = None
        if report_date_str:
            # Tìm bản ghi cũ trùng ngày (nếu có)
            instance = DailyCampaignStat.objects.filter(report_date=report_date_str).first()
            
        # Truyền instance vào form: 
        # - Nếu instance có giá trị => Django hiểu là UPDATE (Sửa)
        # - Nếu instance là None => Django hiểu là CREATE (Thêm mới)
        form = DailyStatForm(request.POST, instance=instance)
        
        if form.is_valid():
            form.save()
            action = "cập nhật" if instance else "thêm mới"
            messages.success(request, f"Đã {action} báo cáo ngày {report_date_str}")
            return redirect('marketing_dashboard')
        else:
            # Nếu form lỗi, in ra để debug (nếu cần) và báo lỗi
            print(f"Form Errors: {form.errors}")
            messages.error(request, f"Lỗi nhập liệu: {form.errors.as_text()}")
    else:
        form = DailyStatForm(initial={'report_date': today})

    # C. LẤY DỮ LIỆU BÁO CÁO
    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end]).order_by('-report_date')
    
    # Tính tổng KPI
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'),
        sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'),
        sum_comments=Sum('comments'),
        sum_inboxes=Sum('inboxes')
    )
    
    # Tính chỉ số trung bình
    total_spend = totals['sum_spend'] or 0
    total_leads = totals['sum_leads'] or 0
    total_appts = totals['sum_appts'] or 0
    
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0
    
    # D. BIỂU ĐỒ & SO SÁNH
    chart_dates = []
    chart_cpl = []
    chart_leads = []
    enhanced_stats = []
    
    for stat in stats:
        # So sánh với ngày hôm trước
        prev_day = stat.report_date - timedelta(days=1)
        try:
            prev_stat = DailyCampaignStat.objects.get(report_date=prev_day)
            if prev_stat.leads > 0:
                trend_lead = ((stat.leads - prev_stat.leads) / prev_stat.leads) * 100
            else:
                trend_lead = 100 if stat.leads > 0 else 0
        except DailyCampaignStat.DoesNotExist:
            trend_lead = 0
            
        stat.trend_lead = trend_lead
        enhanced_stats.append(stat)
        
        # Dữ liệu biểu đồ (đảo ngược để hiển thị đúng chiều thời gian nếu cần, hoặc giữ nguyên tùy chart)
        # Ở đây ta insert(0) để đưa ngày cũ lên đầu danh sách cho biểu đồ
        chart_dates.insert(0, stat.report_date.strftime('%d/%m'))
        chart_cpl.insert(0, float(stat.cost_per_lead))
        chart_leads.insert(0, stat.leads)

    context = {
        'stats': enhanced_stats,
        'form': form,
        'totals': totals,
        'avg_cpl': avg_cpl,
        'avg_cpa': avg_cpa,
        'chart_dates': chart_dates,
        'chart_cpl': chart_cpl,
        'chart_leads': chart_leads,
        'date_start': date_start,
        'date_end': date_end,
    }
    return render(request, 'marketing/dashboard.html', context)

# --- 2. XÓA BÁO CÁO ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE'])
def delete_report(request, pk):
    report = get_object_or_404(DailyCampaignStat, pk=pk)
    date_str = report.report_date
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, f"Đã xóa báo cáo ngày {date_str}")
        
    return redirect('marketing_dashboard')