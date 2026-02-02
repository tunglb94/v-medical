from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
import json

from .models import MarketingTask, DailyCampaignStat, ContentAd, TaskFeedback
from apps.sales.models import Service, Order
from apps.customers.models import Customer
# [THÊM MỚI] Import Appointment để đếm số lịch hẹn
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users
from .forms import DailyStatForm, MarketingTaskForm, ContentAdForm
from apps.authentication.models import User 

# --- 1. DASHBOARD MARKETING (NHẬP LIỆU & TỔNG QUAN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'TELESALE', 'CONTENT', 'EDITOR', 'DESIGNER'])
def marketing_dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    date_start = request.GET.get('date_start', str(start_of_month))
    date_end = request.GET.get('date_end', str(today))
    marketer_query = request.GET.get('marketer', '')
    service_query = request.GET.get('service', '')
    platform_query = request.GET.get('platform', '') 
    
    # Xử lý Form thêm/sửa báo cáo hàng ngày
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
    if platform_query:
        stats = stats.filter(platform=platform_query)
        
    stats = stats.order_by('-report_date', 'platform', 'marketer')
    
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'), 
        sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'), 
        sum_comments=Sum('comments'), 
        sum_inboxes=Sum('inboxes'),
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
    
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0
    avg_cpa = (total_spend / total_appts) if total_appts > 0 else 0
    avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    avg_ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0
    
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
    
    platform_choices = DailyCampaignStat.Platform.choices

    context = {
        'stats': stats, 'form': form, 'totals': totals,
        'avg_cpl': avg_cpl, 'avg_cpa': avg_cpa,
        'avg_cpc': avg_cpc, 'avg_ctr': avg_ctr, 
        'chart_dates': chart_dates, 'chart_cpl': chart_cpl, 'chart_leads': chart_leads,
        'date_start': date_start, 'date_end': date_end,
        'marketer_query': marketer_query, 'service_query': service_query,
        'platform_query': platform_query,
        'platform_choices': platform_choices
    }
    return render(request, 'marketing/dashboard.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def delete_report(request, pk):
    get_object_or_404(DailyCampaignStat, pk=pk).delete()
    messages.success(request, "Đã xóa báo cáo.")
    return redirect('marketing_dashboard')

# --- 2. BÁO CÁO HIỆU QUẢ MARKETING (ROI & PHỄU CHUYỂN ĐỔI) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'MANAGER'])
def marketing_report(request):
    """
    Báo cáo tổng hợp: Data -> Hẹn -> Đơn hàng (Phễu vận hành)
    """
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    date_start_str = request.GET.get('date_start', str(start_of_month))
    date_end_str = request.GET.get('date_end', str(today))

    try:
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d').date()
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d').date()
    except:
        date_start, date_end = start_of_month, today

    # 1. Tổng Chi phí Marketing (Để hiển thị tổng quan nếu có)
    campaign_stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end])
    total_cost = campaign_stats.aggregate(Sum('spend_amount'))['spend_amount__sum'] or 0

    # 2. Tổng Data Leads (Từ Customer)
    customers = Customer.objects.filter(created_at__date__range=[date_start, date_end])
    total_leads = customers.count()
    
    # Group Leads theo Fanpage
    leads_by_page = {}
    cus_grouped = customers.values('fanpage').annotate(count=Count('id'))
    for item in cus_grouped:
        leads_by_page[item['fanpage']] = item['count']

    # 3. [MỚI] Tổng Lịch Hẹn (Appointment)
    # Đếm số lịch hẹn được tạo ra trong khoảng thời gian này
    appointments = Appointment.objects.filter(
        created_at__date__range=[date_start, date_end]
    ).select_related('customer')

    appts_by_page = {}
    total_appts = 0
    for appt in appointments:
        if appt.customer and appt.customer.fanpage:
            fp = appt.customer.fanpage
            appts_by_page[fp] = appts_by_page.get(fp, 0) + 1
            total_appts += 1

    # 4. Tổng Doanh thu & Đơn hàng (Order)
    orders = Order.objects.filter(
        order_date__range=[date_start, date_end],
        is_paid=True
    ).select_related('customer')
    
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Group Doanh thu & Số đơn theo Fanpage
    revenue_by_page = {}
    orders_count_by_page = {}
    
    for order in orders:
        if order.customer and order.customer.fanpage:
            fp = order.customer.fanpage
            revenue_by_page[fp] = revenue_by_page.get(fp, 0) + order.total_amount
            orders_count_by_page[fp] = orders_count_by_page.get(fp, 0) + 1

    # 5. Tổng hợp bảng chi tiết Fanpage
    report_data = []
    # Lấy tất cả Fanpage xuất hiện trong Data, Hẹn hoặc Đơn
    all_fanpages = set(list(leads_by_page.keys()) + list(appts_by_page.keys()) + list(orders_count_by_page.keys()))
    
    fanpage_choices = dict(Customer.Fanpage.choices)

    for fp_code in all_fanpages:
        if not fp_code: continue
        
        leads = leads_by_page.get(fp_code, 0)
        appts = appts_by_page.get(fp_code, 0)
        orders_count = orders_count_by_page.get(fp_code, 0)
        revenue = revenue_by_page.get(fp_code, 0)
        
        # --- TÍNH TỶ LỆ CHUYỂN ĐỔI ---
        
        # 1. Tỷ lệ Data -> Hẹn (Chất lượng Data + Telesale)
        rate_lead_to_appt = (appts / leads * 100) if leads > 0 else 0
        
        # 2. Tỷ lệ Hẹn -> Đơn (Tỷ lệ đến khám + Chốt Sale tại phòng)
        rate_appt_to_order = (orders_count / appts * 100) if appts > 0 else 0

        # Doanh thu trung bình mỗi Data (Revenue per Lead)
        rpl = (revenue / leads) if leads > 0 else 0

        # Trung bình đơn (AOV)
        aov = (revenue / orders_count) if orders_count > 0 else 0

        # Đánh giá chất lượng sơ bộ dựa trên tỷ lệ hẹn
        quality_tag = "Bình thường"
        if rate_lead_to_appt > 30: quality_tag = "🔥 Data xịn"
        elif rate_lead_to_appt > 15: quality_tag = "✅ Ổn định"
        elif rate_lead_to_appt < 5 and leads > 10: quality_tag = "⚠️ Rác nhiều"

        report_data.append({
            'code': fp_code,
            'name': fanpage_choices.get(fp_code, fp_code),
            'leads': leads,
            'appts': appts,
            'orders': orders_count,
            'revenue': revenue,
            'aov': aov,
            'rate_lead_to_appt': rate_lead_to_appt,
            'rate_appt_to_order': rate_appt_to_order,
            'rpl': rpl,
            'quality': quality_tag
        })

    # Sắp xếp theo số lượng Data giảm dần
    report_data.sort(key=lambda x: x['leads'], reverse=True)

    # 6. Chỉ số tổng quan toàn cục
    global_percent_cost = (total_cost / total_revenue * 100) if total_revenue > 0 else 0
    
    # Tỷ lệ chuyển đổi Data -> Hẹn toàn hệ thống
    global_conversion_appt = (total_appts / total_leads * 100) if total_leads > 0 else 0

    # --- CHUẨN BỊ DỮ LIỆU BIỂU ĐỒ (Group theo ngày) ---
    # 1. Data Leads theo ngày
    daily_leads = customers.values('created_at__date').annotate(count=Count('id')).order_by('created_at__date')
    leads_map = {item['created_at__date'].strftime('%Y-%m-%d'): item['count'] for item in daily_leads}

    # 2. Doanh thu theo ngày
    daily_revenue = orders.values('order_date').annotate(total=Sum('total_amount')).order_by('order_date')
    
    # [FIX LỖI] Chuyển Decimal sang float tại đây để JSON serialize được
    rev_map = {item['order_date'].strftime('%Y-%m-%d'): float(item['total'] or 0) for item in daily_revenue}

    # 3. Tạo danh sách ngày liên tục từ start đến end
    chart_labels = []
    chart_data_leads = []
    chart_data_revenue = []
    
    current_date = date_start
    while current_date <= date_end:
        d_str = current_date.strftime('%Y-%m-%d')
        d_label = current_date.strftime('%d/%m') # Nhãn hiển thị (VD: 01/01)
        
        chart_labels.append(d_label)
        chart_data_leads.append(leads_map.get(d_str, 0))
        # Do rev_map đã chứa float nên get ra sẽ là float (hoặc 0)
        chart_data_revenue.append(rev_map.get(d_str, 0))
        
        current_date += timedelta(days=1)

    context = {
        'date_start': date_start_str,
        'date_end': date_end_str,
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_leads': total_leads,
        'total_appts': total_appts,
        'global_percent_cost': global_percent_cost,
        'global_conversion_appt': global_conversion_appt,
        'report_data': report_data,
        'chart_labels': json.dumps(chart_labels),
        'chart_data_leads': json.dumps(chart_data_leads),
        'chart_data_revenue': json.dumps(chart_data_revenue), # Giờ đã an toàn
    }
    return render(request, 'marketing/report.html', context)

# --- 3. QUẢN LÝ CONTENT ADS & LỊCH ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER'])
def content_ads_list(request):
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

# --- 4. SỬA TASK & LƯU FEEDBACK ---
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

        new_feedback = request.POST.get('new_feedback')
        if new_feedback and new_feedback.strip():
            TaskFeedback.objects.create(
                task=task,
                user=request.user,
                content=new_feedback.strip()
            )
        
        messages.success(request, f"Đã cập nhật công việc: {task.title}")
        
    return redirect('content_ads_list')

# --- 5. API LẤY LỊCH SỬ FEEDBACK ---
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