from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Subquery, OuterRef, Count
from django.utils import timezone
from datetime import timedelta, date
import re # <--- Import Regex để check SĐT

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

    # Thêm select_related để lấy thông tin Sale nhanh hơn
    customers = Customer.objects.select_related('assigned_telesale').all()

    # Tìm kiếm
    search_query = request.GET.get('q', '')
    if search_query:
        customers = customers.filter(
            Q(phone__icontains=search_query) | Q(name__icontains=search_query)
        )

    # Bộ lọc
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

    # Xử lý chọn khách
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

    # Lưu kết quả gọi
    if request.method == "POST" and selected_customer:
        selected_customer.name = request.POST.get('cus_name', selected_customer.name)
        selected_customer.phone = request.POST.get('cus_phone', selected_customer.phone)
        selected_customer.gender = request.POST.get('cus_gender', selected_customer.gender)
        selected_customer.address = request.POST.get('cus_address', selected_customer.address)
        selected_customer.city = request.POST.get('cus_city', selected_customer.city)
        selected_customer.skin_condition = request.POST.get('cus_skin', selected_customer.skin_condition)
        
        # --- CẬP NHẬT FANPAGE KHI SỬA ---
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
        'fanpage_choices': Customer.Fanpage.choices, # <--- TRUYỀN DATA FANPAGE
        'status_choices': CallLog.CallStatus.choices,
        'gender_choices': Customer.Gender.choices,
        'telesales_list': telesales_list,
        'today_str': today.strftime('%Y-%m-%d')
    }
    return render(request, 'telesales/dashboard.html', context)


# --- 2. THÊM KHÁCH THỦ CÔNG (CÓ CHECK REGEX SĐT) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN'])
def add_customer_manual(request):
    if request.method == "POST":
        phone = request.POST.get('phone', '').strip() # Xóa khoảng trắng thừa
        name = request.POST.get('name')
        telesale_id = request.POST.get('telesale_id')
        
        if not phone or not name:
            messages.error(request, "Thiếu Tên hoặc SĐT!")
            return redirect('telesale_home')

        # --- CHECK ĐỊNH DẠNG SĐT ---
        if not re.match(r'^0\d{9}$', phone):
            messages.error(request, f"SĐT '{phone}' không hợp lệ! Phải là 10 số và bắt đầu bằng số 0.")
            return redirect('telesale_home')

        # --- KIỂM TRA TRÙNG SỐ ---
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
                
                # --- LƯU FANPAGE KHI TẠO MỚI ---
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


# --- 3. BÁO CÁO TELESALE ---
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
    
    # Thống kê Nguồn
    source_stats = customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_labels = [dict(Customer.Source.choices).get(x['source']) for x in source_stats]
    source_data = [x['count'] for x in source_stats]

    # --- THỐNG KÊ FANPAGE (MỚI) ---
    fanpage_stats = customers.values('fanpage').annotate(count=Count('id')).order_by('-count')
    fanpage_dict = dict(Customer.Fanpage.choices)
    fanpage_data_list = []
    
    for item in fanpage_stats:
        code = item['fanpage']
        label = fanpage_dict.get(code, "Chưa xác định") if code else "Chưa xác định"
        fanpage_data_list.append({
            'label': label,
            'count': item['count']
        })
    # ------------------------------

    city_stats = customers.values('city').annotate(count=Count('id')).order_by('-count')[:5]
    gender_stats = customers.values('gender').annotate(count=Count('id'))
    
    age_groups = {'18-25': 0, '26-35': 0, '36-45': 0, '46+': 0, 'Unknown': 0}
    for cus in customers:
        age = cus.age
        if not age: age_groups['Unknown'] += 1
        elif 18 <= age <= 25: age_groups['18-25'] += 1
        elif 26 <= age <= 35: age_groups['26-35'] += 1
        elif 36 <= age <= 45: age_groups['36-45'] += 1
        else: age_groups['46+'] += 1
    
    status_stats = logs.values('status').annotate(count=Count('id')).order_by('-count')
    status_dict = dict(CallLog.CallStatus.choices)
    status_data_list = [{'label': status_dict.get(x['status']), 'value': x['count']} for x in status_stats]

    telesales = User.objects.filter(role='TELESALE')
    performance_data = []
    
    for sale in telesales:
        assigned_count = customers.filter(assigned_telesale=sale).count()
        sale_logs = logs.filter(caller=sale)
        total_calls = sale_logs.count()
        booked_calls = sale_logs.filter(status='BOOKED').count()
        rate = (booked_calls / total_calls * 100) if total_calls > 0 else 0
        
        if assigned_count > 0 or total_calls > 0:
            performance_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}",
                'username': sale.username,
                'assigned': assigned_count,
                'total_calls': total_calls,
                'booked': booked_calls,
                'rate': round(rate, 1)
            })
    
    performance_data.sort(key=lambda x: x['rate'], reverse=True)

    context = {
        'date_start': date_start_str,
        'date_end': date_end_str,
        'total_leads': total_leads,
        'source_labels': source_labels,
        'source_data': source_data,
        'fanpage_data_list': fanpage_data_list, # <--- TRUYỀN DATA MỚI
        'city_stats': city_stats,
        'gender_stats': gender_stats,
        'age_groups': age_groups,
        'status_data_list': status_data_list,
        'performance_data': performance_data,
    }
    return render(request, 'telesales/report.html', context)