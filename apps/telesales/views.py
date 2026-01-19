from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Subquery, OuterRef, Count
from django.utils import timezone
from datetime import timedelta, date
import re 

from apps.customers.models import Customer
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.authentication.decorators import allowed_users

User = get_user_model()

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN', 'RECEPTIONIST', 'CONSULTANT'])
def telesale_dashboard(request):
    today = timezone.now().date()
    
    telesales_list = User.objects.filter(role='TELESALE', is_active=True)
    city_list_raw = Customer.objects.exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True).distinct().order_by('city')
    city_list = [{'code': city, 'label': city} for city in city_list_raw] 

    customers = Customer.objects.select_related('assigned_telesale').all()

    if request.user.role == 'TELESALE' and getattr(request.user, 'team', None):
        teammate_ids = User.objects.filter(team=request.user.team).values_list('id', flat=True)
        customers = customers.filter(
            Q(assigned_telesale_id__in=teammate_ids) | Q(assigned_telesale__isnull=True)
        )
        telesales_list = telesales_list.filter(team=request.user.team)

    search_query = request.GET.get('q', '')
    if search_query:
        customers = customers.filter(
            Q(phone__icontains=search_query) | Q(name__icontains=search_query)
        )

    req_date_start = request.GET.get('date_start')
    req_date_end = request.GET.get('date_end')
    req_source = request.GET.get('source')
    req_fanpage = request.GET.get('fanpage')
    req_city = request.GET.get('city')
    req_gender = request.GET.get('gender')
    req_age_min = request.GET.get('age_min')
    req_age_max = request.GET.get('age_max')
    req_status = request.GET.get('status')
    req_skin = request.GET.get('skin')
    
    req_report_city = request.GET.get('filter_city')
    req_report_gender = request.GET.get('filter_gender')
    req_report_fanpage = request.GET.get('filter_fanpage')
    req_report_telesale = request.GET.get('filter_telesale')
    req_report_status = request.GET.get('filter_status')
    req_report_skin = request.GET.get('filter_skin')
    
    status_to_filter = req_status if req_status else req_report_status
    skin_to_filter = req_skin if req_skin else req_report_skin

    is_drill_down = any([req_source, req_fanpage, req_city, req_gender, req_age_min, req_age_max, req_status, req_skin])
    is_report_filter_active = any([req_report_city, req_report_gender, req_report_fanpage, req_report_telesale, req_report_status, req_report_skin, req_date_start, req_date_end])
    is_report_context = is_drill_down or is_report_filter_active

    if is_report_context:
        if req_date_start and req_date_end:
            customers = customers.filter(created_at__date__range=[req_date_start, req_date_end])

        if req_source: customers = customers.filter(source=req_source)
        
        city_to_filter = req_city if req_city else req_report_city
        if city_to_filter: 
            if city_to_filter == 'None': customers = customers.filter(city__isnull=True)
            else: customers = customers.filter(city=city_to_filter) 
        
        gender_to_filter = req_gender if req_gender else req_report_gender
        if gender_to_filter: customers = customers.filter(gender=gender_to_filter)
        
        fanpage_to_filter = req_fanpage if req_fanpage else req_report_fanpage
        if fanpage_to_filter:
            if fanpage_to_filter == 'None': customers = customers.filter(fanpage__isnull=True)
            else: customers = customers.filter(fanpage=fanpage_to_filter)

        if req_report_telesale: customers = customers.filter(assigned_telesale_id=req_report_telesale)
        
        if skin_to_filter:
            if skin_to_filter == 'None': customers = customers.filter(skin_condition__isnull=True)
            else: customers = customers.filter(skin_condition=skin_to_filter)

        if req_age_min or req_age_max:
            current_year = today.year
            if req_age_min:
                max_dob_year = current_year - int(req_age_min)
                customers = customers.filter(dob__year__lte=max_dob_year)
            if req_age_max:
                min_dob_year = current_year - int(req_age_max)
                customers = customers.filter(dob__year__gte=min_dob_year)

        if status_to_filter and not request.GET.get('type'):
            latest_log = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time')
            customers = customers.annotate(
                current_status=Subquery(latest_log.values('status')[:1])
            )
            if status_to_filter == 'NEW':
                customers = customers.filter(Q(current_status='NEW') | Q(current_status__isnull=True))
            else:
                customers = customers.filter(current_status=status_to_filter)
        
    req_type = request.GET.get('type')
    
    if req_type:
        filter_type = req_type
    elif not is_report_context and not search_query:
        filter_type = 'new'
    else:
        filter_type = ''

    if filter_type == 'new':
        customers = customers.filter(created_at__date=today)
        
    elif filter_type == 'old':
        customers = customers.exclude(created_at__date=today)
        
    elif filter_type == 'callback':
        last_log = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time')
        customers = customers.annotate(
            last_status=Subquery(last_log.values('status')[:1]),
            last_callback_time=Subquery(last_log.values('callback_time')[:1])
        )
        customers = customers.filter(
            last_status='FOLLOW_UP',
            last_callback_time__date=today
        )
        customers = customers.order_by('last_callback_time')

    elif filter_type == 'birthday':
        customers = customers.filter(dob__day=today.day, dob__month=today.month)
        
    elif filter_type == 'dormant':
        cutoff_date = today - timedelta(days=90)
        customers = customers.annotate(
            last_visit=Max('appointments__appointment_date', filter=Q(appointments__status__in=['ARRIVED', 'COMPLETED']))
        ).filter(last_visit__lt=cutoff_date).exclude(appointments__status='SCHEDULED', appointments__appointment_date__gte=today)

    if not (filter_type == 'callback'):
        customers = customers.order_by('-created_at')

    selected_customer = None
    call_history = []
    
    customer_id = request.GET.get('id')
    if customer_id:
        try:
            selected_customer = get_object_or_404(Customer, id=int(float(str(customer_id).replace(',', '.'))))
        except (ValueError, TypeError, Customer.DoesNotExist):
            pass
    elif customers.exists():
        selected_customer = customers.first()

    if selected_customer:
        call_history = CallLog.objects.filter(customer=selected_customer).order_by('-call_time')

    if request.method == "POST" and selected_customer:
        selected_customer.name = request.POST.get('cus_name', selected_customer.name)
        selected_customer.phone = request.POST.get('cus_phone', selected_customer.phone)
        selected_customer.gender = request.POST.get('cus_gender', selected_customer.gender)
        selected_customer.address = request.POST.get('cus_address', selected_customer.address)
        selected_customer.city = request.POST.get('cus_city', selected_customer.city)
        selected_customer.skin_condition = request.POST.get('cus_skin', selected_customer.skin_condition)
        selected_customer.fanpage = request.POST.get('cus_fanpage', selected_customer.fanpage)
        
        new_telesale_id = request.POST.get('assigned_telesale_id')
        if new_telesale_id and new_telesale_id.isdigit():
            selected_customer.assigned_telesale_id = int(new_telesale_id)
        else:
            selected_customer.assigned_telesale_id = None

        dob_val = request.POST.get('cus_dob')
        if dob_val: selected_customer.dob = dob_val
        selected_customer.save()

        note_content = request.POST.get('note')
        status_value = request.POST.get('status')
        appointment_date = request.POST.get('appointment_date')
        callback_date = request.POST.get('callback_date') 
        
        if status_value == 'BOOKED':
            if not appointment_date:
                messages.error(request, "LỖI: Chưa chọn ngày giờ hẹn!")
                return redirect(request.get_full_path())
            
            Appointment.objects.create(
                customer=selected_customer,
                appointment_date=appointment_date,
                status='SCHEDULED',
                created_by=request.user,
                assigned_consultant=request.user 
            )
            messages.success(request, f"Đã chốt hẹn: {selected_customer.name}")

        log = CallLog(
            customer=selected_customer,
            caller=request.user,
            status=status_value,
            note=note_content
        )
        
        if status_value == 'FOLLOW_UP':
             if callback_date:
                 log.callback_time = callback_date
                 messages.success(request, f"Đã lưu lịch hẹn gọi lại vào: {callback_date}")
             else:
                 messages.warning(request, "Lưu ý: Bạn chưa chọn giờ gọi lại.")

        log.save()
        
        if status_value != 'BOOKED' and status_value != 'FOLLOW_UP':
            messages.success(request, "Đã lưu kết quả.")

        return redirect(request.get_full_path())

    current_params = request.GET.copy()
    if 'id' in current_params:
        del current_params['id']
    filter_query_string = current_params.urlencode() 

    context = {
        'customers': customers,
        'selected_customer': selected_customer,
        'call_history': call_history,
        'search_query': search_query,
        'filter_type': filter_type, 
        'filter_query_string': filter_query_string,
        'source_choices': Customer.Source.choices,
        'skin_choices': Customer.SkinIssue.choices, 
        'fanpage_choices': Customer.Fanpage.choices,
        'status_choices': CallLog.CallStatus.choices,
        'gender_choices': Customer.Gender.choices,
        'telesales_list': telesales_list,
        'city_list': city_list, 
        'today_str': today.strftime('%Y-%m-%d'),
        'req_report_city': req_report_city,
        'req_report_gender': req_report_gender,
        'req_report_fanpage': req_report_fanpage,
        'req_report_telesale': req_report_telesale,
        'req_report_status': req_report_status,
        'req_report_skin': req_report_skin,
        'req_date_start': req_date_start,
        'req_date_end': req_date_end,
    }
    return render(request, 'telesales/dashboard.html', context)


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN', 'RECEPTIONIST', 'CONSULTANT'])
def add_customer_manual(request):
    if request.method == "POST":
        phone = request.POST.get('phone', '').strip()
        name = request.POST.get('name')
        telesale_id = request.POST.get('telesale_id')
        
        if not phone or not name:
            messages.error(request, "Thiếu Tên hoặc SĐT!")
            return redirect('telesale_home')

        if not re.match(r'^0\d{9}$', phone):
            messages.error(request, f"SĐT '{phone}' không hợp lệ!")
            return redirect('telesale_home')

        existing_customer = Customer.objects.filter(phone=phone).first()
        if existing_customer:
            messages.warning(request, f"SĐT {phone} đã có trên hệ thống!")
            return redirect(f'/telesale/?id={existing_customer.id}')

        try:
            assigned_user_id = telesale_id if telesale_id else request.user.id
            new_customer = Customer.objects.create(
                name=name, 
                phone=phone,
                gender=request.POST.get('gender', 'FEMALE'),
                dob=request.POST.get('dob') or None,
                city=request.POST.get('city'),
                address=request.POST.get('address'),
                source=request.POST.get('source'),
                fanpage=request.POST.get('fanpage'), 
                skin_condition=request.POST.get('skin_condition'),
                note_telesale=request.POST.get('note_telesale'),
                assigned_telesale_id=assigned_user_id
            )
            messages.success(request, f"Đã thêm khách mới!")
            return redirect(f'/telesale/?id={new_customer.id}')
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            
    return redirect('telesale_home')


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE', 'RECEPTIONIST', 'CONSULTANT'])
def telesale_report(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    date_start_str = request.GET.get('date_start', str(start_of_month))
    date_end_str = request.GET.get('date_end', str(today))
    
    req_city = request.GET.get('filter_city')
    req_gender = request.GET.get('filter_gender')
    req_fanpage = request.GET.get('filter_fanpage')
    req_telesale = request.GET.get('filter_telesale')
    req_skin = request.GET.get('filter_skin')
    req_status = request.GET.get('filter_status')
    
    customers = Customer.objects.filter(created_at__date__range=[date_start_str, date_end_str])

    if request.user.role == 'TELESALE' and getattr(request.user, 'team', None):
        teammate_ids = User.objects.filter(team=request.user.team).values_list('id', flat=True)
        customers = customers.filter(
            Q(assigned_telesale_id__in=teammate_ids) | Q(assigned_telesale__isnull=True)
        )
    
    latest_log_subquery = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time').values('status')[:1]
    customers = customers.annotate(final_status=Subquery(latest_log_subquery))

    if req_city:
        if req_city == 'None': customers = customers.filter(city__isnull=True)
        else: customers = customers.filter(city=req_city)
    if req_gender: customers = customers.filter(gender=req_gender)
    if req_fanpage: customers = customers.filter(fanpage=req_fanpage)
    if req_telesale: customers = customers.filter(assigned_telesale_id=req_telesale)
    if req_skin: customers = customers.filter(skin_condition=req_skin)
    
    if req_status:
        if req_status == 'NEW':
            customers = customers.filter(Q(final_status='NEW') | Q(final_status__isnull=True))
        else:
            customers = customers.filter(final_status=req_status)
    
    total_leads = customers.count()
    
    source_stats = customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_data = [{'code': x['source'], 'label': dict(Customer.Source.choices).get(x['source'], 'Khác'), 'count': x['count'], 'percent': round(x['count']/total_leads*100, 1) if total_leads else 0} for x in source_stats]

    fanpage_stats = customers.values('fanpage').annotate(count=Count('id')).order_by('-count')
    fanpage_dict = dict(Customer.Fanpage.choices)
    unmapped_fanpage_count = 0
    final_fanpage_data = []
    for x in fanpage_stats:
        code = x['fanpage']
        label = fanpage_dict.get(code, 'UNMAPPED_CODE') 
        if label == 'UNMAPPED_CODE' or not code:
            unmapped_fanpage_count += x['count']
            continue
        final_fanpage_data.append({'code': code, 'label': label, 'count': x['count'], 'percent': round(x['count']/total_leads*100, 1) if total_leads else 0})
    if unmapped_fanpage_count > 0:
        final_fanpage_data.append({'code': 'None', 'label': "Chưa cập nhật/Mã lỗi", 'count': unmapped_fanpage_count, 'percent': round(unmapped_fanpage_count/total_leads*100, 1) if total_leads else 0})
    final_fanpage_data.sort(key=lambda x: x['count'], reverse=True)
    fanpage_data = final_fanpage_data

    city_stats_raw = customers.values('city').annotate(count=Count('id')).order_by('-count')
    city_stats = [{'city': i['city'], 'count': i['count'], 'code': 'None' if not i['city'] else i['city']} for i in city_stats_raw]
    
    gender_stats_raw = customers.values('gender').annotate(count=Count('id'))
    gender_data = [{'code': x['gender'], 'label': dict(Customer.Gender.choices).get(x['gender'], 'Không rõ'), 'count': x['count']} for x in gender_stats_raw]

    age_groups = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '55+': 0, 'Unknown': 0}
    for cus in customers:
        age = cus.age
        if not age: age_groups['Unknown'] += 1
        elif 18 <= age <= 25: age_groups['18-25'] += 1
        elif 26 <= age <= 35: age_groups['26-35'] += 1
        elif 36 <= age <= 45: age_groups['36-45'] += 1
        elif 46 <= age <= 55: age_groups['46-55'] += 1
        else: age_groups['55+'] += 1
        
    skin_stats_raw = customers.values('skin_condition').annotate(count=Count('id')).order_by('-count')
    skin_data = [{'code': x['skin_condition'], 'label': dict(Customer.SkinIssue.choices).get(x['skin_condition'], 'Không rõ'), 'count': x['count'], 'percent': round(x['count']/total_leads*100, 1) if total_leads else 0} for x in skin_stats_raw]

    status_counts_query = customers.values('final_status').annotate(total=Count('id'))
    status_map = {item['final_status']: item['total'] for item in status_counts_query}
    data_quality_list = []
    total_counted = 0
    for code, label in CallLog.CallStatus.choices:
        if code == 'NEW': continue
        count = status_map.get(code, 0) 
        if count > 0:
            data_quality_list.append({'code': code, 'label': label, 'count': count, 'rate': round(count/total_leads*100, 1) if total_leads else 0})
            total_counted += count
    count_uncontacted = total_leads - total_counted
    if count_uncontacted > 0:
        data_quality_list.append({'code': 'NEW', 'label': 'Mới / Chưa gọi', 'count': count_uncontacted, 'rate': round(count_uncontacted/total_leads*100, 1) if total_leads else 0})
    data_quality_list.sort(key=lambda x: x['count'], reverse=True)

    telesales = User.objects.filter(role='TELESALE')
    if request.user.role == 'TELESALE' and getattr(request.user, 'team', None):
        telesales = telesales.filter(team=request.user.team)

    filtered_customer_ids = customers.values_list('id', flat=True) 
    logs = CallLog.objects.filter(customer__id__in=filtered_customer_ids) 
    
    performance_data = []
    for sale in telesales:
        assigned_count = customers.filter(assigned_telesale=sale).count() 
        sale_logs = logs.filter(caller=sale)
        total_calls = sale_logs.count()
        
        booked_unique = Appointment.objects.filter(
            created_at__date__range=[date_start_str, date_end_str], 
            customer__assigned_telesale=sale,
            customer__id__in=filtered_customer_ids,
            status__in=['SCHEDULED', 'ARRIVED', 'IN_CONSULTATION', 'COMPLETED']
        ).values('customer').distinct().count()

        rate_on_assigned = (booked_unique / assigned_count * 100) if assigned_count > 0 else 0
        if assigned_count > 0 or total_calls > 0 or booked_unique > 0:
            performance_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}", 'username': sale.username,
                'assigned': assigned_count, 'total_calls': total_calls, 'booked': booked_unique, 'rate': round(rate_on_assigned, 1)
            })
    performance_data.sort(key=lambda x: x['booked'], reverse=True)

    recare_data = []
    
    period_logs = CallLog.objects.filter(call_time__date__range=[date_start_str, date_end_str])
    period_bookings = Appointment.objects.filter(
        created_at__date__range=[date_start_str, date_end_str],
        status__in=['SCHEDULED', 'ARRIVED', 'IN_CONSULTATION', 'COMPLETED']
    )

    if req_city:
        if req_city == 'None': 
            period_logs = period_logs.filter(customer__city__isnull=True)
            period_bookings = period_bookings.filter(customer__city__isnull=True)
        else: 
            period_logs = period_logs.filter(customer__city=req_city)
            period_bookings = period_bookings.filter(customer__city=req_city)

    if req_gender:
        period_logs = period_logs.filter(customer__gender=req_gender)
        period_bookings = period_bookings.filter(customer__gender=req_gender)

    if req_fanpage:
        period_logs = period_logs.filter(customer__fanpage=req_fanpage)
        period_bookings = period_bookings.filter(customer__fanpage=req_fanpage)
        
    if req_skin:
        period_logs = period_logs.filter(customer__skin_condition=req_skin)
        period_bookings = period_bookings.filter(customer__skin_condition=req_skin)

    if req_telesale:
        period_logs = period_logs.filter(customer__assigned_telesale_id=req_telesale)
        period_bookings = period_bookings.filter(customer__assigned_telesale_id=req_telesale)
    elif request.user.role == 'TELESALE' and getattr(request.user, 'team', None):
        teammate_ids = User.objects.filter(team=request.user.team).values_list('id', flat=True)
        period_logs = period_logs.filter(Q(customer__assigned_telesale_id__in=teammate_ids) | Q(customer__assigned_telesale__isnull=True))
        period_bookings = period_bookings.filter(Q(customer__assigned_telesale_id__in=teammate_ids) | Q(customer__assigned_telesale__isnull=True))

    for sale in telesales:
        my_logs = period_logs.filter(caller=sale)
        total_calls_period = my_logs.count()
        total_customers_touched = my_logs.values('customer').distinct().count()
        my_bookings = period_bookings.filter(created_by=sale).count()
        conversion_rate = (my_bookings / total_customers_touched * 100) if total_customers_touched > 0 else 0
        
        if total_calls_period > 0 or my_bookings > 0:
            recare_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}",
                'username': sale.username,
                'total_calls': total_calls_period,
                'customers_touched': total_customers_touched,
                'booked': my_bookings,
                'rate': round(conversion_rate, 1)
            })
            
    recare_data.sort(key=lambda x: x['booked'], reverse=True)

    telesales_list = User.objects.filter(role='TELESALE', is_active=True).order_by('first_name')
    if request.user.role == 'TELESALE' and getattr(request.user, 'team', None):
        telesales_list = telesales_list.filter(team=request.user.team)

    context = {
        'date_start': date_start_str,
        'date_end': date_end_str,
        'total_leads': total_leads,
        'source_data': source_data,
        'fanpage_data': fanpage_data,
        'city_stats': city_stats,
        'gender_data': gender_data,
        'age_groups': age_groups,
        'skin_data': skin_data,
        'data_quality_list': data_quality_list,
        'performance_data': performance_data,
        'recare_data': recare_data, 
        'telesales_list': telesales_list,
        'gender_choices': Customer.Gender.choices,
        'fanpage_choices': Customer.Fanpage.choices,
        'skin_choices': Customer.SkinIssue.choices,
        'status_choices': CallLog.CallStatus.choices,
        'req_city': req_city,
        'req_gender': req_gender,
        'req_fanpage': req_fanpage,
        'req_telesale': req_telesale,
        'req_skin': req_skin,
        'req_status': req_status, 
    }
    return render(request, 'telesales/report.html', context)