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
from apps.customers.models import Customer, Fanpage
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users
from .forms import DailyStatForm, MarketingTaskForm, ContentAdForm
from apps.authentication.models import User 

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

    stats = DailyCampaignStat.objects.filter(report_date__range=[date_start, date_end])
    if marketer_query: stats = stats.filter(marketer__icontains=marketer_query)
    if service_query: stats = stats.filter(service__icontains=service_query)
    if platform_query: stats = stats.filter(platform=platform_query)
    stats = stats.order_by('-report_date', 'platform', 'marketer')
    
    totals = stats.aggregate(
        sum_spend=Sum('spend_amount'), sum_leads=Sum('leads'),
        sum_appts=Sum('appointments'), sum_comments=Sum('comments'), 
        sum_inboxes=Sum('inboxes'), sum_impressions=Sum('impressions'),
        sum_clicks=Sum('clicks'), sum_views=Sum('views')
    )
    for key in totals:
        if totals[key] is None: totals[key] = 0

    # --- LOGIC CHIA DOANH THU THEO TỪNG FANPAGE THỰC TẾ ---
    revenue_map = {} 
    all_orders = Order.objects.filter(
        order_date__range=[date_start, date_end]
    ).select_related('customer').prefetch_related('customer__fanpages', 'customer__fanpages__assigned_marketer')

    for order in all_orders:
        cus = order.customer
        pages = cus.fanpages.all()
        num_pages = pages.count()
        rev = float(order.actual_revenue or 0)
        
        if num_pages > 0:
            split_revenue = rev / num_pages
            for fp in pages:
                if fp.assigned_marketer:
                    # Lấy Họ Tên để map với tên Marketer nhập trong Stats
                    key = f"{fp.assigned_marketer.last_name} {fp.assigned_marketer.first_name}".strip()
                    if not key: key = fp.assigned_marketer.username
                else:
                    key = "Chưa gán nhân sự"
                revenue_map[key] = revenue_map.get(key, 0) + split_revenue
        else:
            revenue_map["Chưa tick Fanpage"] = revenue_map.get("Chưa tick Fanpage", 0) + rev

    marketer_stats_qs = stats.values('marketer').annotate(
        total_spend=Sum('spend_amount'), total_leads=Sum('leads'), total_appts=Sum('appointments')
    ).order_by('-total_spend')

    report_marketers = []
    for item in marketer_stats_qs:
        m_name = item['marketer']
        if not m_name: continue
        sp = round(float(item['total_spend'] or 0) * 1.1)
        
        # So khớp doanh thu (Lấy tên gần đúng)
        rev = 0
        for k, v in revenue_map.items():
            if m_name.lower() in k.lower() or k.lower() in m_name.lower():
                rev = v
                break
        
        report_marketers.append({
            'name': m_name, 'spend': sp, 'leads': item['total_leads'],
            'appts': item['total_appts'], 'revenue': rev,
            'roas': (sp / float(rev) * 100) if rev > 0 else 0
        })

    # Giữ nguyên logic chart và context cũ
    chart_data_qs = stats.values('report_date').annotate(daily_leads=Sum('leads'), daily_spend=Sum('spend_amount')).order_by('report_date')
    chart_dates, chart_cpl, chart_leads = [], [], []
    for item in chart_data_qs:
        d_leads = item['daily_leads'] or 0
        d_spend_vat = round(float(item['daily_spend'] or 0) * 1.1)
        chart_dates.append(item['report_date'].strftime('%d/%m'))
        chart_leads.append(d_leads)
        chart_cpl.append(round(d_spend_vat / d_leads) if d_leads > 0 else 0) 
    
    context = {
        'stats': stats, 'form': form, 'totals': totals,
        'avg_cpl': (totals['sum_spend'] / totals['sum_leads']) if totals['sum_leads'] > 0 else 0,
        'avg_cpc': (totals['sum_spend'] / totals['sum_clicks']) if totals['sum_clicks'] > 0 else 0,
        'avg_ctr': (totals['sum_clicks'] / totals['sum_impressions'] * 100) if totals['sum_impressions'] > 0 else 0, 
        'chart_dates': chart_dates, 'chart_cpl': chart_cpl, 'chart_leads': chart_leads,
        'date_start': date_start, 'date_end': date_end,
        'marketer_query': marketer_query, 'service_query': service_query,
        'platform_query': platform_query, 'platform_choices': DailyCampaignStat.Platform.choices,
        'report_marketers': report_marketers
    }
    return render(request, 'marketing/dashboard.html', context)

# --- GIỮ NGUYÊN TOÀN BỘ HÀM PHÍA DƯỚI CỦA BẠN ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING'])
def delete_report(request, pk):
    get_object_or_404(DailyCampaignStat, pk=pk).delete()
    messages.success(request, "Đã xóa báo cáo.")
    return redirect('marketing_dashboard')

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
    for cus in customers.prefetch_related('fanpages'):
        pages = cus.fanpages.all()
        n = pages.count()
        if n > 0:
            for fp in pages: leads_by_page[fp.code] = leads_by_page.get(fp.code, 0) + (1/n)
        else:
            fp = cus.fanpage
            if fp: leads_by_page[fp] = leads_by_page.get(fp, 0) + 1

    appointments = Appointment.objects.filter(created_at__date__range=[date_start, date_end]).select_related('customer').prefetch_related('customer__fanpages')
    appts_by_page, total_appts = {}, 0
    for appt in appointments:
        if appt.customer:
            pages = appt.customer.fanpages.all()
            n = pages.count()
            if n > 0:
                for fp in pages: appts_by_page[fp.code] = appts_by_page.get(fp.code, 0) + (1/n)
            else:
                fp = appt.customer.fanpage
                if fp: appts_by_page[fp] = appts_by_page.get(fp, 0) + 1
            total_appts += 1

    orders = Order.objects.filter(order_date__range=[date_start, date_end]).select_related('customer').prefetch_related('customer__fanpages')
    total_revenue = orders.aggregate(Sum('actual_revenue'))['actual_revenue__sum'] or 0
    revenue_by_page, orders_count_by_page = {}, {}
    for order in orders:
        if order.customer:
            pages = order.customer.fanpages.all()
            n = pages.count()
            if n > 0:
                split_rev = float(order.actual_revenue) / n
                for fp in pages:
                    revenue_by_page[fp.code] = revenue_by_page.get(fp.code, 0) + split_rev
                    orders_count_by_page[fp.code] = orders_count_by_page.get(fp.code, 0) + (1/n)
            else:
                fp = order.customer.fanpage
                if fp:
                    revenue_by_page[fp] = revenue_by_page.get(fp, 0) + float(order.actual_revenue)
                    orders_count_by_page[fp] = orders_count_by_page.get(fp, 0) + 1

    report_data = []
    all_fanpages = set(list(leads_by_page.keys()) + list(appts_by_page.keys()) + list(orders_count_by_page.keys()))
    fanpage_choices = dict(Customer.FanpageChoices.choices)

    for fp_code in all_fanpages:
        if not fp_code: continue
        leads, appts, orders_count = leads_by_page.get(fp_code, 0), appts_by_page.get(fp_code, 0), orders_count_by_page.get(fp_code, 0)
        revenue = revenue_by_page.get(fp_code, 0)
        rate_lead_to_appt = (appts / leads * 100) if leads > 0 else 0
        quality_tag = "🔥 Data xịn" if rate_lead_to_appt > 30 else "Bình thường"
        fp_obj = Fanpage.objects.filter(code=fp_code).first()
        report_data.append({
            'code': fp_code, 'name': fp_obj.name if fp_obj else fanpage_choices.get(fp_code, fp_code),
            'leads': round(leads, 1), 'appts': round(appts, 1), 'orders': round(orders_count, 1),
            'revenue': revenue, 'aov': (revenue / orders_count) if orders_count > 0 else 0,
            'rate_lead_to_appt': rate_lead_to_appt, 'rate_appt_to_order': (orders_count / appts * 100) if appts > 0 else 0,
            'rpl': (revenue / leads) if leads > 0 else 0, 'quality': quality_tag
        })

    report_data.sort(key=lambda x: x['leads'], reverse=True)
    daily_leads = customers.values('created_at__date').annotate(count=Count('id')).order_by('created_at__date')
    leads_map = {item['created_at__date'].strftime('%Y-%m-%d'): item['count'] for item in daily_leads}
    daily_revenue = orders.values('order_date').annotate(total=Sum('actual_revenue')).order_by('order_date')
    rev_map = {item['order_date'].strftime('%Y-%m-%d'): float(item['total'] or 0) for item in daily_revenue}

    chart_labels, chart_data_leads, chart_data_revenue = [], [], []
    curr = date_start
    while curr <= date_end:
        d_str, d_label = curr.strftime('%Y-%m-%d'), curr.strftime('%d/%m')
        chart_labels.append(d_label)
        chart_data_leads.append(leads_map.get(d_str, 0))
        chart_data_revenue.append(rev_map.get(d_str, 0))
        curr += timedelta(days=1)

    context = {
        'date_start': date_start_str, 'date_end': date_end_str, 'total_cost': total_cost,
        'total_revenue': total_revenue, 'total_leads': total_leads, 'total_appts': total_appts,
        'global_percent_cost': (total_cost / total_revenue * 100) if total_revenue > 0 else 0,
        'global_conversion_appt': (total_appts / total_leads * 100) if total_leads > 0 else 0,
        'report_data': report_data, 'chart_labels': json.dumps(chart_labels),
        'chart_data_leads': json.dumps(chart_data_leads), 'chart_data_revenue': json.dumps(chart_data_revenue),
        'fanpage_choices': Customer.FanpageChoices.choices,
    }
    return render(request, 'marketing/report.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER'])
def content_ads_list(request):
    services = Service.objects.all()
    staffs = User.objects.filter(is_active=True).exclude(is_superuser=True)
    tasks = MarketingTask.objects.all().select_related('pic_content', 'pic_design', 'pic_ads', 'created_by', 'service')
    keyword = request.GET.get('keyword', '')
    if keyword: tasks = tasks.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
    tasks = tasks.order_by('-created_at')
    if request.method == 'POST':
        MarketingTask.objects.create(title=request.POST.get('title'), platform=request.POST.get('platform'), status=request.POST.get('status'), content=request.POST.get('content'), service_id=request.POST.get('service_id') or None, created_by=request.user)
        messages.success(request, "Đã thêm công việc mới!")
        return redirect('content_ads_list')
    return render(request, 'marketing/content_ads.html', {'tasks': tasks, 'services': services, 'staffs': staffs})

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER'])
def content_ads_edit(request, pk):
    task = get_object_or_404(MarketingTask, pk=pk)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.save()
        messages.success(request, f"Đã cập nhật công việc: {task.title}")
    return redirect('content_ads_list')

@login_required(login_url='/auth/login/')
def get_task_feedback_api(request, task_id):
    feedbacks = TaskFeedback.objects.filter(task_id=task_id).select_related('user').order_by('-created_at')
    data = [{'user': fb.user.username, 'content': fb.content, 'time': fb.created_at.strftime("%H:%M %d/%m")} for fb in feedbacks]
    return JsonResponse(data, safe=False)

@login_required(login_url='/auth/login/')
def content_ads_delete(request, pk):
    get_object_or_404(MarketingTask, pk=pk).delete()
    messages.success(request, "Đã xóa công việc.")
    return redirect('content_ads_list')

@login_required(login_url='/auth/login/')
def marketing_workspace(request):
    tasks, events, today = MarketingTask.objects.all(), [], timezone.now().date()
    for t in tasks:
        if t.start_date:
            events.append({'title': t.title, 'start': t.start_date.strftime('%Y-%m-%d'), 'color': '#4e73df'})
    return render(request, 'marketing/workspace.html', {'events_json': json.dumps(events)})

@login_required(login_url='/auth/login/')
def get_marketing_tasks_api(request):
    return JsonResponse([], safe=False)