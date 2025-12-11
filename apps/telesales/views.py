# v-medical/apps/telesales/views.py

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

# --- 1. DASHBOARD TELESALE (XỬ LÝ FULL: FILTER CƠ BẢN + DRILL-DOWN TỪ REPORT) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN'])
def telesale_dashboard(request):
    today = timezone.now().date()
    telesales_list = User.objects.filter(role='TELESALE', is_active=True)

    customers = Customer.objects.select_related('assigned_telesale').all()

    # --- A. TÌM KIẾM (SEARCH) ---
    search_query = request.GET.get('q', '')
    if search_query:
        customers = customers.filter(
            Q(phone__icontains=search_query) | Q(name__icontains=search_query)
        )

    # --- B. BỘ LỌC TỪ BÁO CÁO (DRILL-DOWN FILTER) ---
    # Nhận các tham số khi user click vào số liệu bên trang Report
    req_date_start = request.GET.get('date_start')
    req_date_end = request.GET.get('date_end')
    req_source = request.GET.get('source')
    req_fanpage = request.GET.get('fanpage')
    req_city = request.GET.get('city')
    req_gender = request.GET.get('gender')
    req_age_min = request.GET.get('age_min')
    req_age_max = request.GET.get('age_max')
    req_status = request.GET.get('status') # Trạng thái cuối (Booked, Far away...)

    # Kiểm tra xem request này có phải là lọc từ báo cáo không
    is_report_filter = any([req_source, req_fanpage, req_city, req_gender, req_age_min, req_age_max, req_status])

    if is_report_filter:
        # 1. Lọc theo Date Range (Luôn lọc theo created_at trong drill-down, trừ khi lọc theo trạng thái)
        if req_date_start and req_date_end:
            # Nếu lọc theo trạng thái (req_status), ta cần xem khách hàng có log TRONG KỲ không
            if req_status:
                # CHỈ LỌC THEO call_time khi có req_status
                customers = customers.filter(call_logs__call_time__date__range=[req_date_start, req_date_end]).distinct()
            else:
                # LỌC THEO created_at cho các thuộc tính khác (source, fanpage, city, gender, age)
                customers = customers.filter(created_at__date__range=[req_date_start, req_date_end])

        # 2. Lọc thuộc tính cơ bản
        if req_source: customers = customers.filter(source=req_source)
        if req_fanpage: 
            # XỬ LÝ TRƯỜNG HỢP FANPAGE KHÁC/NULL
            if req_fanpage == 'None': customers = customers.filter(fanpage__isnull=True)
            else: customers = customers.filter(fanpage=req_fanpage)
            
        if req_city: 
            if req_city == 'None': customers = customers.filter(city__isnull=True)
            else: customers = customers.filter(city=req_city) # Lọc chính xác
        if req_gender: customers = customers.filter(gender=req_gender)

        # 3. Lọc Độ tuổi (Tính toán từ năm sinh)
        if req_age_min or req_age_max:
            current_year = today.year
            if req_age_min:
                # Tuổi >= X thì Năm sinh <= (Năm nay - X)
                max_dob_year = current_year - int(req_age_min)
                customers = customers.filter(dob__year__lte=max_dob_year)
            if req_age_max:
                # Tuổi <= Y thì Năm sinh >= (Năm nay - Y)
                min_dob_year = current_year - int(req_age_max)
                customers = customers.filter(dob__year__gte=min_dob_year)

        # 4. Lọc Trạng thái (Logic Smart: Lấy trạng thái CUỐI CÙNG)
        if req_status:
            # Subquery lấy log mới nhất của từng khách
            latest_log = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time')
            customers = customers.annotate(
                current_status=Subquery(latest_log.values('status')[:1])
            ).filter(current_status=req_status)
            
    else:
        # --- C. BỘ LỌC MẶC ĐỊNH (KHI DÙNG DASHBOARD BÌNH THƯỜNG) ---
        # SỬA LỖI TẠI ĐÂY: Nếu đang tìm kiếm (có search_query) thì KHÔNG áp dụng bộ lọc ngày tháng mặc định
        if not search_query:
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
    
    # Sắp xếp mặc định: Mới nhất lên đầu
    customers = customers.order_by('-created_at')

    # --- D. XỬ LÝ CHỌN KHÁCH & HIỂN THỊ CHI TIẾT ---
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

    # --- E. XỬ LÝ POST: LƯU LOG / SỬA KHÁCH / ĐẶT HẸN ---
    if request.method == "POST" and selected_customer:
        selected_customer.name = request.POST.get('cus_name', selected_customer.name)
        selected_customer.phone = request.POST.get('cus_phone', selected_customer.phone)
        selected_customer.gender = request.POST.get('cus_gender', selected_customer.gender)
        selected_customer.address = request.POST.get('cus_address', selected_customer.address)
        selected_customer.city = request.POST.get('cus_city', selected_customer.city)
        selected_customer.skin_condition = request.POST.get('cus_skin', selected_customer.skin_condition)
        selected_customer.fanpage = request.POST.get('cus_fanpage', selected_customer.fanpage)
        
        # --- CẬP NHẬT SALE PHỤ TRÁCH (MỚI) ---
        new_telesale_id = request.POST.get('assigned_telesale_id')
        if new_telesale_id and new_telesale_id.isdigit(): # Kiểm tra id là số
            selected_customer.assigned_telesale_id = int(new_telesale_id)
        else:
            selected_customer.assigned_telesale_id = None
        # --------------------------------------

        dob_val = request.POST.get('cus_dob')
        if dob_val: selected_customer.dob = dob_val
        selected_customer.save()

        note_content = request.POST.get('note')
        status_value = request.POST.get('status')
        appointment_date = request.POST.get('appointment_date')
        
        if status_value == 'BOOKED':
            if not appointment_date:
                messages.error(request, "LỖI: Chưa chọn ngày giờ hẹn!")
                # Redirect giữ nguyên các tham số query hiện tại
                return redirect(request.get_full_path())
            
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

        return redirect(request.get_full_path())

    context = {
        'customers': customers,
        'selected_customer': selected_customer,
        'call_history': call_history,
        'search_query': search_query,
        'filter_type': request.GET.get('type', 'new'),
        'source_choices': Customer.Source.choices,
        'skin_choices': Customer.SkinIssue.choices,
        'fanpage_choices': Customer.Fanpage.choices,
        'status_choices': CallLog.CallStatus.choices,
        'gender_choices': Customer.Gender.choices,
        'telesales_list': telesales_list,
        'today_str': today.strftime('%Y-%m-%d'),
        # Truyền thêm các tham số drill-down để template có thể dùng nếu cần
        'req_date_start': req_date_start,
        'req_date_end': req_date_end,
    }
    return render(request, 'telesales/dashboard.html', context)


# --- 2. THÊM KHÁCH THỦ CÔNG (LOGIC GỐC: REGEX & CHECK TRÙNG) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['TELESALE', 'ADMIN'])
def add_customer_manual(request):
    # Code giữ nguyên
    # ...
    if request.method == "POST":
        phone = request.POST.get('phone', '').strip()
        name = request.POST.get('name')
        telesale_id = request.POST.get('telesale_id')
        
        if not phone or not name:
            messages.error(request, "Thiếu Tên hoặc SĐT!")
            return redirect('telesale_home')

        # Check định dạng SĐT
        if not re.match(r'^0\d{9}$', phone):
            messages.error(request, f"SĐT '{phone}' không hợp lệ! Phải là 10 số và bắt đầu bằng số 0.")
            return redirect('telesale_home')

        # Check trùng
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


# --- 3. BÁO CÁO TELESALE (LOGIC SMART + HỖ TRỢ CLICK CHI TIẾT) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE'])
def telesale_report(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    date_start_str = request.GET.get('date_start', str(start_of_month))
    date_end_str = request.GET.get('date_end', str(today))
    
    # --- XỬ LÝ CÁC BỘ LỌC NÂNG CAO MỚI ---
    req_city = request.GET.get('filter_city')
    req_gender = request.GET.get('filter_gender')
    req_fanpage = request.GET.get('filter_fanpage')
    req_telesale = request.GET.get('filter_telesale')
    
    # 1. Data đầu vào (Input): Tập khách hàng được tạo trong kỳ BÁO CÁO
    customers = Customer.objects.filter(created_at__date__range=[date_start_str, date_end_str])
    
    # ÁP DỤNG CÁC BỘ LỌC NÂNG CAO VÀO TẬP DỮ LIỆU ĐẦU VÀO
    if req_city:
        if req_city == 'None': customers = customers.filter(city__isnull=True)
        # SỬA: Lọc chính xác cho City
        else: customers = customers.filter(city=req_city) 
    if req_gender: customers = customers.filter(gender=req_gender)
    if req_fanpage: customers = customers.filter(fanpage=req_fanpage)
    if req_telesale: customers = customers.filter(assigned_telesale_id=req_telesale)
    
    # 2. Data hoạt động (Logs)
    # Lấy TẤT CẢ log của TẬP KHÁCH HÀNG ĐÃ LỌC, không cần lọc theo date range của log
    # để đảm bảo lấy được trạng thái cuối cùng chính xác.
    logs = CallLog.objects.filter(customer__in=customers.values('pk')) 

    total_leads = customers.count()
    
    # --- THỐNG KÊ NGUỒN (Có mã code) ---
    source_stats = customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_data = []
    for x in source_stats:
        code = x['source']
        label = dict(Customer.Source.choices).get(code, 'Khác')
        percent = round(x['count']/total_leads*100, 1) if total_leads else 0
        source_data.append({'code': code, 'label': label, 'count': x['count'], 'percent': percent})

    # --- THỐNG KÊ FANPAGE (Có mã code) ---
    fanpage_stats = customers.values('fanpage').annotate(count=Count('id')).order_by('-count')
    fanpage_dict = dict(Customer.Fanpage.choices)
    
    unmapped_fanpage_count = 0
    final_fanpage_data = []

    for x in fanpage_stats:
        code = x['fanpage']
        label = fanpage_dict.get(code, 'UNMAPPED_CODE') 
        
        # SỬA: Nếu mã là 'UNMAPPED_CODE' (Không khớp choices) hoặc `None` (chưa gán) thì gom lại
        if label == 'UNMAPPED_CODE' or not code:
            unmapped_fanpage_count += x['count']
            continue

        # Nếu là mã hợp lệ, thêm vào danh sách kết quả cuối cùng
        percent = round(x['count']/total_leads*100, 1) if total_leads else 0
        final_fanpage_data.append({'code': code, 'label': label, 'count': x['count'], 'percent': percent})

    # Thêm nhóm mã không xác định (Unmapped) đã được hợp nhất vào danh sách kết quả (nếu có)
    if unmapped_fanpage_count > 0:
        unmapped_percent = round(unmapped_fanpage_count/total_leads*100, 1) if total_leads else 0
        final_fanpage_data.append({
            'code': 'None', # Dùng 'None' để drill-down vào khách hàng chưa có Fanpage
            'label': "Chưa cập nhật/Mã lỗi",
            'count': unmapped_fanpage_count, 
            'percent': unmapped_percent
        })
        
    final_fanpage_data.sort(key=lambda x: x['count'], reverse=True)
    fanpage_data = final_fanpage_data

    # --- THỐNG KÊ TỈNH THÀNH ---
    # SỬA: Thay thế logic cũ để xử lý khách hàng có city=None
    city_stats_raw = customers.values('city').annotate(count=Count('id')).order_by('-count')
    city_stats = []
    for item in city_stats_raw:
        city = item['city']
        # Dùng mã 'None' cho drill-down
        code = 'None' if city is None or city == '' else city
        city_stats.append({'city': city, 'count': item['count'], 'code': code})
    
    # --- THỐNG KÊ GIỚI TÍNH (Có mã code) ---
    gender_stats_raw = customers.values('gender').annotate(count=Count('id'))
    gender_data = []
    for x in gender_stats_raw:
        code = x['gender']
        label = dict(Customer.Gender.choices).get(code, 'Không rõ')
        gender_data.append({'code': code, 'label': label, 'count': x['count']})

    # --- THỐNG KÊ ĐỘ TUỔI ---
    age_groups = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '55+': 0, 'Unknown': 0}
    for cus in customers:
        age = cus.age
        if not age: age_groups['Unknown'] += 1
        elif 18 <= age <= 25: age_groups['18-25'] += 1
        elif 26 <= age <= 35: age_groups['26-35'] += 1
        elif 36 <= age <= 45: age_groups['36-45'] += 1
        elif 46 <= age <= 55: age_groups['46-55'] += 1
        else: age_groups['55+'] += 1

    # --- CHẤT LƯỢNG DATA (SMART LOGIC: LẤY TRẠNG THÁI MỚI NHẤT) ---
    
    # B1: Lấy trạng thái cuối cùng của các khách hàng TRONG TẬP `customers` đã lọc
    latest_log_subquery = CallLog.objects.filter(
        customer=OuterRef('pk')
    ).order_by('-call_time').values('status')[:1]

    status_counts_query = customers.annotate(
        final_status=Subquery(latest_log_subquery)
    ).values('final_status').annotate(total=Count('id'))

    status_map = {item['final_status']: item['total'] for item in status_counts_query}

    data_quality_list = []
    
    # Khởi tạo tổng số lượng khách hàng chưa được tính
    total_counted = 0
    
    # Lấy tất cả các status trừ NEW
    for code, label in CallLog.CallStatus.choices:
        if code == 'NEW': continue
            
        count = status_map.get(code, 0) 
        if count > 0:
            rate = round(count/total_leads*100, 1) if total_leads else 0
            
            data_quality_list.append({
                'code': code, 
                'label': label,
                'count': count,
                'rate': rate
            })
            total_counted += count

    # Gom các khách hàng còn lại (chưa có log nào (None) + log cuối là NEW)
    count_uncontacted = total_leads - total_counted
    
    if count_uncontacted > 0:
        rate_uncontacted = round(count_uncontacted/total_leads*100, 1) if total_leads else 0
        data_quality_list.append({
            'code': 'NEW', 
            'label': dict(CallLog.CallStatus.choices).get('NEW', 'Mới / Chưa gọi'),
            'count': count_uncontacted,
            'rate': rate_uncontacted
        })

    data_quality_list.sort(key=lambda x: x['count'], reverse=True)
    
    # --- HIỆU SUẤT TELESALE (ĐÃ SỬA: ĐẾM DỰA TRÊN LỊCH HẸN THẬT) ---
    telesales = User.objects.filter(role='TELESALE')
    performance_data = []
    
    for sale in telesales:
        # 1. Data được phân bổ (Tính trên tập customers đã lọc input)
        assigned_count = customers.filter(assigned_telesale=sale).count() 
        
        # 2. Tổng cuộc gọi (Vẫn lấy từ Log)
        # Lấy log của khách hàng trong tập `customers` đã lọc và có người gọi là `sale`
        sale_logs = logs.filter(caller=sale)
        total_calls = sale_logs.count()
        
        # 3. SỐ LỊCH ĐẶT (Đếm số khách hàng DUY NHẤT đã được đặt lịch trong kỳ)
        booked_unique = Appointment.objects.filter(
            # Lọc lịch hẹn được TẠO trong khoảng thời gian báo cáo
            created_at__date__range=[date_start_str, date_end_str],
            # Khách hàng này phải nằm trong TẬP customers ĐÃ LỌC
            customer__in=customers,
            # Và khách hàng đó do Telesale này phụ trách (hoặc Telesale này là người tạo lịch - tạm giữ logic cũ)
            customer__assigned_telesale=sale,
            # Lọc theo trạng thái là Đã đặt lịch (SCHEDULED)
            status='SCHEDULED' 
        ).values('customer').distinct().count()
        
        # Tính tỷ lệ chốt
        rate_on_assigned = (booked_unique / assigned_count * 100) if assigned_count > 0 else 0
        
        # Chỉ hiển thị nhân viên có data hoặc có gọi điện
        if assigned_count > 0 or total_calls > 0 or booked_unique > 0:
            performance_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}",
                'username': sale.username,
                'assigned': assigned_count,
                'total_calls': total_calls,
                'booked': booked_unique, 
                'rate': round(rate_on_assigned, 1)
            })
    
    performance_data.sort(key=lambda x: x['booked'], reverse=True)
    
    # --- CHUẨN BỊ DỮ LIỆU CHO BỘ LỌC NÂNG CAO TRONG TEMPLATE ---
    telesales_list = User.objects.filter(role='TELESALE', is_active=True).order_by('first_name')


    context = {
        'date_start': date_start_str,
        'date_end': date_end_str,
        'total_leads': total_leads,
        'source_data': source_data,
        'fanpage_data': fanpage_data,
        'city_stats': city_stats,
        'gender_data': gender_data,
        'age_groups': age_groups,
        'data_quality_list': data_quality_list,
        'performance_data': performance_data,
        
        # DỮ LIỆU CHO BỘ LỌC NÂNG CAO
        'telesales_list': telesales_list,
        'gender_choices': Customer.Gender.choices,
        'fanpage_choices': Customer.Fanpage.choices,
        'req_city': req_city, # Giá trị lọc đã chọn
        'req_gender': req_gender,
        'req_fanpage': req_fanpage,
        'req_telesale': req_telesale,
    }
    return render(request, 'telesales/report.html', context)