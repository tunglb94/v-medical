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

# --- 1. DASHBOARD TELESALE ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN'])
def telesale_dashboard(request):
    today = timezone.now().date()
    telesales_list = User.objects.filter(role='TELESALE', is_active=True)

    customers = Customer.objects.select_related('assigned_telesale').all()

    search_query = request.GET.get('q', '')
    if search_query:
        customers = customers.filter(
            Q(phone__icontains=search_query) | Q(name__icontains=search_query)
        )

    filter_type = request.GET.get('type', 'new') 
    if filter_type == 'new':
        customers = customers.filter(created_at__date=today)
    elif filter_type == 'old':
        customers = customers.exclude(created_at__date=today)
    elif filter_type == 'callback':
        last_log = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time')
        customers = customers.annotate(
            last_status=Subquery(last_log.values('status')[:1])
        ).filter(last_status__in=['FOLLOW_UP', 'BUSY', 'CONSULTING'])
    elif filter_type == 'birthday':
        customers = customers.filter(dob__day=today.day, dob__month=today.month)
    elif filter_type == 'dormant':
        cutoff_date = today - timedelta(days=90)
        customers = customers.annotate(
            last_visit=Max('appointments__appointment_date', filter=Q(appointments__status__in=['ARRIVED', 'COMPLETED']))
        ).filter(last_visit__lt=cutoff_date).exclude(appointments__status='SCHEDULED', appointments__appointment_date__gte=today)
    
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
        
        dob_val = request.POST.get('cus_dob')
        if dob_val: selected_customer.dob = dob_val
        selected_customer.save()

        note_content = request.POST.get('note')
        status_value = request.POST.get('status')
        appointment_date = request.POST.get('appointment_date')
        
        if status_value == 'BOOKED':
            if not appointment_date:
                messages.error(request, "LỖI: Chưa chọn ngày giờ hẹn!")
                return redirect(f'/telesale/?id={selected_customer.id}&type={filter_type}&q={search_query}')
            
            Appointment.objects.create(
                customer=selected_customer,
                appointment_date=appointment_date,
                status='SCHEDULED',
                created_by=request.user,
                assigned_consultant=request.user
            )
            messages.success(request, f"Đã chốt hẹn: {selected_customer.name}")

        CallLog.objects.create(
            customer=selected_customer,
            caller=request.user,
            status=status_value,
            note=note_content
        )
        
        if status_value != 'BOOKED':
            messages.success(request, "Đã lưu kết quả.")

        return redirect(f'/telesale/?id={selected_customer.id}&type={filter_type}&q={search_query}')

    context = {
        'customers': customers,
        'selected_customer': selected_customer,
        'call_history': call_history,
        'search_query': search_query,
        'filter_type': filter_type,
        'source_choices': Customer.Source.choices,
        'skin_choices': Customer.SkinIssue.choices,
        'fanpage_choices': Customer.Fanpage.choices,
        'status_choices': CallLog.CallStatus.choices,
        'gender_choices': Customer.Gender.choices,
        'telesales_list': telesales_list,
        'today_str': today.strftime('%Y-%m-%d')
    }
    return render(request, 'telesales/dashboard.html', context)


# --- 2. THÊM KHÁCH THỦ CÔNG ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN'])
def add_customer_manual(request):
    if request.method == "POST":
        phone = request.POST.get('phone', '').strip()
        name = request.POST.get('name')
        telesale_id = request.POST.get('telesale_id')
        
        if not phone or not name:
            messages.error(request, "Thiếu Tên hoặc SĐT!")
            return redirect('telesale_home')

        if not re.match(r'^0\d{9}$', phone):
            messages.error(request, f"SĐT '{phone}' không hợp lệ! Phải là 10 số và bắt đầu bằng số 0.")
            return redirect('telesale_home')

        existing_customer = Customer.objects.filter(phone=phone).first()
        if existing_customer:
            messages.warning(request, f"SĐT {phone} đã có trên hệ thống! Đang chuyển tới hồ sơ khách hàng này.")
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


# --- 3. BÁO CÁO TELESALE CHI TIẾT (ĐÃ SỬA: ĐẦY ĐỦ TRƯỜNG) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE'])
def telesale_report(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    date_start_str = request.GET.get('date_start', str(start_of_month))
    date_end_str = request.GET.get('date_end', str(today))
    
    customers = Customer.objects.filter(created_at__date__range=[date_start_str, date_end_str])
    logs = CallLog.objects.filter(call_time__date__range=[date_start_str, date_end_str])

    total_leads = customers.count()
    
    # 1. THỐNG KÊ NGUỒN & FANPAGE
    source_stats = customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_data = []
    for x in source_stats:
        label = dict(Customer.Source.choices).get(x['source'], 'Khác')
        percent = round(x['count']/total_leads*100, 1) if total_leads else 0
        source_data.append({'label': label, 'count': x['count'], 'percent': percent})

    fanpage_stats = customers.values('fanpage').annotate(count=Count('id')).order_by('-count')
    fanpage_dict = dict(Customer.Fanpage.choices)
    fanpage_data = []
    for x in fanpage_stats:
        label = fanpage_dict.get(x['fanpage'], "Chưa xác định")
        percent = round(x['count']/total_leads*100, 1) if total_leads else 0
        fanpage_data.append({'label': label, 'count': x['count'], 'percent': percent})

    # 2. THỐNG KÊ DEMOGRAPHIC
    city_stats = customers.values('city').annotate(count=Count('id')).order_by('-count')
    
    gender_stats_raw = customers.values('gender').annotate(count=Count('id'))
    gender_data = []
    for x in gender_stats_raw:
        label = dict(Customer.Gender.choices).get(x['gender'], 'Không rõ')
        gender_data.append({'label': label, 'count': x['count']})

    age_groups = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '55+': 0, 'Unknown': 0}
    for cus in customers:
        age = cus.age
        if not age: age_groups['Unknown'] += 1
        elif 18 <= age <= 25: age_groups['18-25'] += 1
        elif 26 <= age <= 35: age_groups['26-35'] += 1
        elif 36 <= age <= 45: age_groups['36-45'] += 1
        elif 46 <= age <= 55: age_groups['46-55'] += 1
        else: age_groups['55+'] += 1

    # 3. CHẤT LƯỢNG DATA (FULL TOÀN BỘ TRƯỜNG)
    # Tự động lấy tất cả các lựa chọn trong CallStatus để không bao giờ bị thiếu
    data_quality_list = []
    
    # Những trạng thái muốn loại bỏ khỏi báo cáo (Ví dụ: Mới - vì chưa gọi)
    excluded_statuses = ['NEW'] 
    
    all_statuses = CallLog.CallStatus.choices # Lấy list tuple (code, label) từ Model
    
    for code, label in all_statuses:
        if code in excluded_statuses:
            continue
            
        # Đếm số khách unique có trạng thái này
        count = logs.filter(status=code).values('customer').distinct().count()
        rate = round(count/total_leads*100, 1) if total_leads else 0
        
        data_quality_list.append({
            'code': code,
            'label': label,
            'count': count,
            'rate': rate
        })

    # Sắp xếp theo số lượng giảm dần để dễ nhìn
    data_quality_list.sort(key=lambda x: x['count'], reverse=True)
    
    # 4. HIỆU SUẤT TELESALE
    telesales = User.objects.filter(role='TELESALE')
    performance_data = []
    
    for sale in telesales:
        assigned_count = customers.filter(assigned_telesale=sale).count()
        sale_logs = logs.filter(caller=sale)
        total_calls = sale_logs.count()
        booked_unique = sale_logs.filter(status='BOOKED').values('customer').distinct().count()
        
        rate_on_assigned = (booked_unique / assigned_count * 100) if assigned_count > 0 else 0
        
        if assigned_count > 0 or total_calls > 0:
            performance_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}",
                'username': sale.username,
                'assigned': assigned_count,
                'total_calls': total_calls,
                'booked': booked_unique,
                'rate': round(rate_on_assigned, 1)
            })
    
    performance_data.sort(key=lambda x: x['booked'], reverse=True)

    context = {
        'date_start': date_start_str,
        'date_end': date_end_str,
        'total_leads': total_leads,
        'source_data': source_data,
        'fanpage_data': fanpage_data,
        'city_stats': city_stats,
        'gender_data': gender_data,
        'age_groups': age_groups,
        'data_quality_list': data_quality_list, # <--- Dùng list động này thay vì dict cũ
        'performance_data': performance_data,
    }
    return render(request, 'telesales/report.html', context)