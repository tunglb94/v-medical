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

    # Lọc dữ liệu Báo cáo
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
    
    # --- [CẬP NHẬT] TÍNH DOANH THU & ĐƠN RỚT ---
    revenue_map = {'Vũ': 0, 'Huy': 0, 'Hưng': 0, 'Long': 0}
    failed_map = {'Vũ': 0, 'Huy': 0, 'Hưng': 0, 'Long': 0}
    
    # [QUAN TRỌNG] Lấy TẤT CẢ đơn hàng trong khoảng thời gian này
    # Không dùng is_paid=True để tránh sót đơn nợ
    all_orders = Order.objects.filter(
        order_date__range=[date_start, date_end]
    ).select_related('customer')

    for order in all_orders:
        cus = order.customer
        fp_name = cus.get_fanpage_display() if hasattr(cus, 'get_fanpage_display') else str(cus.fanpage)
        if not fp_name: fp_name = ""
        source_val = str(cus.source) if hasattr(cus, 'source') and cus.source else ""
        
        target_key = None

        # --- QUY TẮC GÁN NHÂN SỰ ---
        if 'Google' in source_val or 'Google' in fp_name:
            target_key = 'Long'
        elif fp_name == "Bác Sĩ Hoàng Vũ - CK I Da Liễu":
            target_key = 'Vũ'
        elif fp_name in ["Ultherapy Prime - Căng Da Không Phẫu Thuật 57A Trần Quốc Thảo", "Cao Trần Quân - Viện Da Liễu V Medical"]:
            target_key = 'Huy'
        elif fp_name == "V - Medical Clinic":
            target_key = 'Hưng'
            
        if target_key:
            # [SỬA LỖI] Cộng doanh thu THỰC THU (actual_revenue) thay vì total_amount
            # Dù đơn chưa xong (nợ), nếu đã đóng tiền thì vẫn tính
            revenue_map[target_key] += order.actual_revenue

            # Đếm đơn rớt: Chỉ đếm nếu KHÔNG thu được đồng nào (Thực thu = 0)
            if order.actual_revenue == 0:
                failed_map[target_key] += 1

    # Thống kê Marketer
    marketer_stats_qs = stats.values('marketer').annotate(
        total_spend=Sum('spend_amount'),
        total_leads=Sum('leads'),
        total_appts=Sum('appointments')
    ).order_by('-total_spend')

    report_marketers = []
    for item in marketer_stats_qs:
        m_name = item['marketer']
        if not m_name: continue
        
        sp = item['total_spend'] or 0
        ld = item['total_leads'] or 0
        ap = item['total_appts'] or 0
        
        rev = 0
        failed = 0
        m_name_lower = m_name.lower()
        
        target_key = None
        if "vũ" in m_name_lower: target_key = 'Vũ'
        elif "huy" in m_name_lower: target_key = 'Huy'
        elif "hưng" in m_name_lower: target_key = 'Hưng'
        elif "long" in m_name_lower: target_key = 'Long'
        
        if target_key:
            rev = revenue_map[target_key]
            failed = failed_map[target_key]
        
        cpl = (sp / ld) if ld > 0 else 0
        cpa = (sp / ap) if ap > 0 else 0
        
        # Tính ROAS (Chi phí / Doanh thu) %
        roas = (sp / rev * 100) if rev > 0 else 0
        
        report_marketers.append({
            'name': m_name,
            'spend': sp,
            'leads': ld,
            'appts': ap,
            'cpl': cpl,
            'cpa': cpa,
            'revenue': rev,
            'failed_orders': failed,
            'roas': roas
        })

    # Biểu đồ
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
        'platform_choices': platform_choices,
        'report_marketers': report_marketers
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
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    date_start_str = request.GET.get('date_start', str(start_of_month))
    date_end_str = request.GET.get('date_end', str(today))

    try:
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d').date()
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d').date()
    except:
        date_start, date_end = start_of_month, today

    campaign_stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end])
    total_cost = campaign_stats.aggregate(Sum('spend_amount'))['spend_amount__sum'] or 0

    customers = Customer.objects.filter(created_at__date__range=[date_start, date_end])
    total_leads = customers.count()
    
    leads_by_page = {}
    cus_grouped = customers.values('fanpage').annotate(count=Count('id'))
    for item in cus_grouped:
        leads_by_page[item['fanpage']] = item['count']

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

    orders = Order.objects.filter(
        order_date__range=[date_start, date_end],
        is_paid=True
    ).select_related('customer')
    
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    revenue_by_page = {}
    orders_count_by_page = {}
    
    for order in orders:
        if order.customer and order.customer.fanpage:
            fp = order.customer.fanpage
            revenue_by_page[fp] = revenue_by_page.get(fp, 0) + order.total_amount
            orders_count_by_page[fp] = orders_count_by_page.get(fp, 0) + 1

    report_data = []
    all_fanpages = set(list(leads_by_page.keys()) + list(appts_by_page.keys()) + list(orders_count_by_page.keys()))
    
    fanpage_choices = dict(Customer.Fanpage.choices)

    for fp_code in all_fanpages:
        if not fp_code: continue
        
        leads = leads_by_page.get(fp_code, 0)
        appts = appts_by_page.get(fp_code, 0)
        orders_count = orders_count_by_page.get(fp_code, 0)
        revenue = revenue_by_page.get(fp_code, 0)
        
        rate_lead_to_appt = (appts / leads * 100) if leads > 0 else 0
        rate_appt_to_order = (orders_count / appts * 100) if appts > 0 else 0
        rpl = (revenue / leads) if leads > 0 else 0
        aov = (revenue / orders_count) if orders_count > 0 else 0

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

    report_data.sort(key=lambda x: x['leads'], reverse=True)

    global_percent_cost = (total_cost / total_revenue * 100) if total_revenue > 0 else 0
    global_conversion_appt = (total_appts / total_leads * 100) if total_leads > 0 else 0

    daily_leads = customers.values('created_at__date').annotate(count=Count('id')).order_by('created_at__date')
    leads_map = {item['created_at__date'].strftime('%Y-%m-%d'): item['count'] for item in daily_leads}

    daily_revenue = orders.values('order_date').annotate(total=Sum('total_amount')).order_by('order_date')
    rev_map = {item['order_date'].strftime('%Y-%m-%d'): float(item['total'] or 0) for item in daily_revenue}

    chart_labels = []
    chart_data_leads = []
    chart_data_revenue = []
    
    current_date = date_start
    while current_date <= date_end:
        d_str = current_date.strftime('%Y-%m-%d')
        d_label = current_date.strftime('%d/%m') 
        
        chart_labels.append(d_label)
        chart_data_leads.append(leads_map.get(d_str, 0))
        chart_data_revenue.append(rev_map.get(d_str, 0))
        
        current_date += timedelta(days=1)

    # TRUY VẤN CHI TIẾT ĐƠN HÀNG KHI LỌC FANPAGE
    detailed_orders = None
    selected_fanpage_name = None
    filter_fanpage = request.GET.get('filter_fanpage')

    if filter_fanpage:
        selected_fanpage_name = fanpage_choices.get(filter_fanpage, filter_fanpage)
        
        detailed_orders = Order.objects.filter(
            order_date__range=[date_start, date_end],
            # [LƯU Ý] Không lọc is_paid để hiện cả đơn rớt
            customer__fanpage=filter_fanpage
        ).select_related('customer', 'service', 'assigned_consultant').order_by('-order_date')

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
        'chart_data_revenue': json.dumps(chart_data_revenue),
        'fanpage_choices': Customer.Fanpage.choices,
        'filter_fanpage': filter_fanpage,
        'detailed_orders': detailed_orders,
        'selected_fanpage_name': selected_fanpage_name,
    }
    return render(request, 'marketing/report.html', context)

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

@login_required(login_url='/auth/login/')
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