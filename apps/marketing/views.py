from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg

from .models import DailyCampaignStat
from .forms import DailyStatForm
from apps.authentication.decorators import allowed_users

# --- 1. DASHBOARD MARKETING ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE'])
def marketing_dashboard(request):
    # A. XỬ LÝ LỌC NGÀY (Mặc định: Từ đầu tháng đến hôm nay)
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    
    # B. XỬ LÝ FORM NHẬP LIỆU (THÊM MỚI HOẶC CẬP NHẬT)
    if request.method == 'POST':
        form = DailyStatForm(request.POST)
        if form.is_valid():
            # Lấy ngày từ form
            date = form.cleaned_data['report_date']
            
            # Hàm update_or_create: Nếu có ngày đó rồi thì Update, chưa thì Create
            obj, created = DailyCampaignStat.objects.update_or_create(
                report_date=date,
                defaults=form.cleaned_data
            )
            
            action = "thêm mới" if created else "cập nhật"
            messages.success(request, f"Đã {action} báo cáo ngày {date}")
            return redirect('marketing_dashboard')
        else:
            messages.error(request, "Lỗi nhập liệu. Vui lòng kiểm tra lại.")
    else:
        # Form mặc định hiển thị ngày hôm nay
        form = DailyStatForm(initial={'report_date': today})

    # C. LẤY DỮ LIỆU BÁO CÁO (Theo ngày lọc)
    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end]).order_by('-report_date')
    
    # Tính tổng KPI trong kỳ (Sum)
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'),
        sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'),
        sum_comments=Sum('comments'),
        sum_inboxes=Sum('inboxes')
    )
    
    # Tính chỉ số trung bình (CPL & CPA)
    total_spend = totals['sum_spend'] or 0
    total_leads = totals['sum_leads'] or 0
    total_appts = totals['sum_appts'] or 0
    
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0 # <--- GIÁ HẸN TB
    
    # D. CHUẨN BỊ DỮ LIỆU BIỂU ĐỒ & SO SÁNH TĂNG GIẢM
    chart_dates = []
    chart_cpl = []
    chart_leads = []
    
    enhanced_stats = [] # Danh sách mới có thêm thuộc tính 'trend'
    
    for stat in stats:
        # 1. Tìm ngày hôm trước để so sánh
        prev_day = stat.report_date - timedelta(days=1)
        try:
            prev_stat = DailyCampaignStat.objects.get(report_date=prev_day)
            
            # Tính % tăng giảm Leads
            if prev_stat.leads > 0:
                trend_lead = ((stat.leads - prev_stat.leads) / prev_stat.leads) * 100
            else:
                trend_lead = 100 if stat.leads > 0 else 0
                
        except DailyCampaignStat.DoesNotExist:
            trend_lead = 0 # Không có ngày hôm trước thì coi như không tăng giảm
            
        # Gán thuộc tính trend vào object (chỉ để hiển thị, không lưu DB)
        stat.trend_lead = trend_lead
        enhanced_stats.append(stat)
        
        # 2. Gom dữ liệu cho biểu đồ (Đảo ngược để ngày cũ bên trái, ngày mới bên phải)
        chart_dates.insert(0, stat.report_date.strftime('%d/%m'))
        chart_cpl.insert(0, float(stat.cost_per_lead))
        chart_leads.insert(0, stat.leads)

    context = {
        'stats': enhanced_stats,
        'form': form,
        'totals': totals,
        'avg_cpl': avg_cpl,
        'avg_cpa': avg_cpa, # <--- Biến mới
        
        # Data cho Chart.js
        'chart_dates': chart_dates,
        'chart_cpl': chart_cpl,
        'chart_leads': chart_leads,
        
        # Giữ lại bộ lọc trên giao diện
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