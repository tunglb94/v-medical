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
    
    # 1. Fetch data for filter dropdowns
    telesales_list = User.objects.filter(role='TELESALE', is_active=True)
    # Lấy danh sách thành phố duy nhất, loại trừ None/chuỗi rỗng
    city_list_raw = Customer.objects.exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True).distinct().order_by('city')
    city_list = [{'code': city, 'label': city} for city in city_list_raw] 

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
    req_status = request.GET.get('status') # Trạng thái cuối (drill-down click)
    req_skin = request.GET.get('skin') # Dịch vụ quan tâm (drill-down click)
    
    # Nhận các bộ lọc nâng cao TỪ FORM REPORT (filter_...)
    req_report_city = request.GET.get('filter_city')
    req_report_gender = request.GET.get('filter_gender')
    req_report_fanpage = request.GET.get('filter_fanpage')
    req_report_telesale = request.GET.get('filter_telesale')
    req_report_status = request.GET.get('filter_status')
    req_report_skin = request.GET.get('filter_skin') # Dịch vụ quan tâm (form filter)
    
    # Xác định trạng thái cuối cùng cần lọc: Ưu tiên Drill-down (req_status)
    status_to_filter = req_status if req_status else req_report_status
    skin_to_filter = req_skin if req_skin else req_report_skin # Ưu tiên Drill-down (req_skin)

    
    # Kiểm tra xem có đang ở ngữ cảnh báo cáo/lọc phức tạp không
    is_drill_down = any([req_source, req_fanpage, req_city, req_gender, req_age_min, req_age_max, req_status, req_skin])
    is_report_filter_active = any([req_report_city, req_report_gender, req_report_fanpage, req_report_telesale, req_report_status, req_report_skin, req_date_start, req_date_end])
    
    is_report_context = is_drill_down or is_report_filter_active

    if is_report_context:
        # 1. Lọc theo Date Range (LUÔN LỌC THEO created_at để khớp với tập dữ liệu đầu vào của Báo cáo)
        if req_date_start and req_date_end:
            customers = customers.filter(created_at__date__range=[req_date_start, req_date_end])

        # 2. Lọc thuộc tính cơ bản
        
        # Lọc Drill-down (Source)
        if req_source: customers = customers.filter(source=req_source)
        
        # Lọc City: Ưu tiên click (req_city) rồi đến form (req_report_city)
        city_to_filter = req_city if req_city else req_report_city
        if city_to_filter: 
            if city_to_filter == 'None': customers = customers.filter(city__isnull=True)
            else: customers = customers.filter(city=city_to_filter) 
        
        # Lọc Gender: Ưu tiên click (req_gender) rồi đến form (req_report_gender)
        gender_to_filter = req_gender if req_gender else req_report_gender
        if gender_to_filter: customers = customers.filter(gender=gender_to_filter)
        
        # Lọc Fanpage: Ưu tiên click (req_fanpage) rồi đến form (req_report_fanpage)
        fanpage_to_filter = req_fanpage if req_fanpage else req_report_fanpage
        if fanpage_to_filter:
            if fanpage_to_filter == 'None': customers = customers.filter(fanpage__isnull=True)
            else: customers = customers.filter(fanpage=fanpage_to_filter)

        # Lọc Telesale phụ trách từ form Report/Dashboard
        if req_report_telesale: customers = customers.filter(assigned_telesale_id=req_report_telesale)
        
        # NEW: Lọc Dịch vụ quan tâm (Skin Issue)
        if skin_to_filter:
            if skin_to_filter == 'None': customers = customers.filter(skin_condition__isnull=True)
            else: customers = customers.filter(skin_condition=skin_to_filter)


        # 3. Lọc Độ tuổi (Tính toán từ năm sinh)
        if req_age_min or req_age_max:
            current_year = today.year
            if req_age_min:
                max_dob_year = current_year - int(req_age_min)
                customers = customers.filter(dob__year__lte=max_dob_year)
            if req_age_max:
                min_dob_year = current_year - int(req_age_max)
                customers = customers.filter(dob__year__gte=min_dob_year)

        # 4. Lọc Trạng thái (Logic Smart: Lấy trạng thái CUỐI CÙNG)
        # [FIX QUAN TRỌNG]: Nếu đang chọn Tab (New/Old/Callback) thì BỎ QUA bộ lọc trạng thái từ báo cáo
        # Để tránh việc lọc cộng dồn (Ví dụ: Tab Cũ + Status FollowUp -> Chỉ ra khách cũ đang FollowUp)
        if status_to_filter and not request.GET.get('type'):
            # Subquery lấy log mới nhất của từng khách
            latest_log = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time')
            customers = customers.annotate(
                current_status=Subquery(latest_log.values('status')[:1])
            )
            
            if status_to_filter == 'NEW':
                # Bao gồm cả khách hàng có log cuối là NEW HOẶC chưa có log nào (current_status IS NULL)
                customers = customers.filter(Q(current_status='NEW') | Q(current_status__isnull=True))
            else:
                # Các trạng thái khác vẫn lọc bình thường
                customers = customers.filter(current_status=status_to_filter)
        
        # Không reset filter_type = '' ở đây nữa

    # --- C. XỬ LÝ CÁC TAB (MỚI / CŨ / DATA CHĂM THÊM) ---
    # Logic: Ưu tiên tham số 'type' từ URL để các Tab luôn hoạt động đúng chức năng
    # Logic này chạy độc lập và sẽ giao (intersection) với bộ lọc báo cáo nếu có
    
    req_type = request.GET.get('type')
    
    # Nếu người dùng bấm Tab, ưu tiên lấy giá trị đó. 
    # Nếu không bấm Tab và cũng không đang lọc báo cáo/tìm kiếm thì mặc định là 'new'
    if req_type:
        filter_type = req_type
    elif not is_report_context and not search_query:
        filter_type = 'new'
    else:
        filter_type = ''

    # --- THỰC HIỆN LỌC THEO TAB ---
    
    if filter_type == 'new':
        # Tab Mới: Chỉ hiển thị data tạo trong ngày hôm nay
        customers = customers.filter(created_at__date=today)
        
    elif filter_type == 'old':
        # Tab Cũ: Chỉ hiển thị data tạo trước ngày hôm nay
        customers = customers.exclude(created_at__date=today)
        
    elif filter_type == 'callback':
        # Tab Data chăm thêm: Data có trạng thái 'FOLLOW_UP' VÀ có lịch hẹn gọi lại LÀ HÔM NAY
        
        # 1. Lấy thông tin log gọi cuối cùng
        last_log = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time')
        
        customers = customers.annotate(
            last_status=Subquery(last_log.values('status')[:1]),
            last_callback_time=Subquery(last_log.values('callback_time')[:1])
        )
        
        # 2. Lọc: Trạng thái là FOLLOW_UP VÀ Ngày hẹn gọi lại = Hôm nay
        customers = customers.filter(
            last_status='FOLLOW_UP',
            last_callback_time__date=today
        )
        
        # 3. Sắp xếp theo giờ hẹn
        customers = customers.order_by('last_callback_time')

    elif filter_type == 'birthday':
        customers = customers.filter(dob__day=today.day, dob__month=today.month)
        
    elif filter_type == 'dormant':
        # Logic data ngủ đông
        cutoff_date = today - timedelta(days=90)
        customers = customers.annotate(
            last_visit=Max('appointments__appointment_date', filter=Q(appointments__status__in=['ARRIVED', 'COMPLETED']))
        ).filter(last_visit__lt=cutoff_date).exclude(appointments__status='SCHEDULED', appointments__appointment_date__gte=today)

    # Sắp xếp mặc định cho các tab khác (Mới nhất lên đầu)
    # Tab callback đã được sort riêng theo giờ hẹn ở trên
    if not (filter_type == 'callback'):
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
        if new_telesale_id and new_telesale_id.isdigit():
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
        callback_date = request.POST.get('callback_date') # Lấy ngày hẹn gọi lại từ form
        
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

        log = CallLog(
            customer=selected_customer,
            caller=request.user,
            status=status_value,
            note=note_content
        )
        
        # Xử lý: CHĂM THÊM (FOLLOW_UP) -> Lưu giờ gọi lại
        if status_value == 'FOLLOW_UP':
             if callback_date:
                 log.callback_time = callback_date
                 messages.success(request, f"Đã lưu lịch hẹn gọi lại vào: {callback_date}")
             else:
                 messages.warning(request, "Lưu ý: Bạn chưa chọn giờ gọi lại (Khách sẽ ở cuối danh sách).")

        log.save()
        
        if status_value != 'BOOKED' and status_value != 'FOLLOW_UP':
            messages.success(request, "Đã lưu kết quả.")

        return redirect(request.get_full_path())

    # --- F. CHUẨN BỊ CHUỖI QUERY CHO CÁC LINK CHỌN KHÁCH HÀNG (QUAN TRỌNG) ---
    current_params = request.GET.copy()
    
    if 'id' in current_params:
        del current_params['id']
        
    filter_query_string = current_params.urlencode() 


    context = {
        'customers': customers,
        'selected_customer': selected_customer,
        'call_history': call_history,
        'search_query': search_query,
        'filter_type': filter_type, # Truyền filter_type đã tính toán
        'filter_query_string': filter_query_string,
        'source_choices': Customer.Source.choices,
        'skin_choices': Customer.SkinIssue.choices, # <-- Đã thêm vào context
        'fanpage_choices': Customer.Fanpage.choices,
        'status_choices': CallLog.CallStatus.choices,
        'gender_choices': Customer.Gender.choices,
        'telesales_list': telesales_list,
        'city_list': city_list, 
        'today_str': today.strftime('%Y-%m-%d'),
        # Truyền các tham số lọc nâng cao hiện tại để giữ trạng thái trên form
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


# --- 2. THÊM KHÁCH THỦ CÔNG (LOGIC GỐC: REGEX & CHECK TRÙNG) ---
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


# --- 3. BÁO CÁO TELESALE (CẬP NHẬT: THÊM BÁO CÁO RE-CARE) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TELESALE'])
def telesale_report(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    date_start_str = request.GET.get('date_start', str(start_of_month))
    date_end_str = request.GET.get('date_end', str(today))
    
    # --- XỬ LÝ CÁC BỘ LỌC NÂNG CAO ---
    req_city = request.GET.get('filter_city')
    req_gender = request.GET.get('filter_gender')
    req_fanpage = request.GET.get('filter_fanpage')
    req_telesale = request.GET.get('filter_telesale')
    req_skin = request.GET.get('filter_skin')
    
    # =================================================================================
    # PHẦN 1: BÁO CÁO CHẤT LƯỢNG DATA (Dựa trên Data MỚI tạo trong kỳ)
    # =================================================================================
    
    # 1. Data đầu vào (Input): Dùng để tính mẫu số (%)
    customers = Customer.objects.filter(created_at__date__range=[date_start_str, date_end_str])
    
    # Áp dụng bộ lọc
    if req_city:
        if req_city == 'None': customers = customers.filter(city__isnull=True)
        else: customers = customers.filter(city=req_city)
    if req_gender: customers = customers.filter(gender=req_gender)
    if req_fanpage: customers = customers.filter(fanpage=req_fanpage)
    if req_telesale: customers = customers.filter(assigned_telesale_id=req_telesale)
    if req_skin: customers = customers.filter(skin_condition=req_skin)
    
    total_leads = customers.count()
    
    # --- THỐNG KÊ NGUỒN ---
    source_stats = customers.values('source').annotate(count=Count('id')).order_by('-count')
    source_data = [{'code': x['source'], 'label': dict(Customer.Source.choices).get(x['source'], 'Khác'), 'count': x['count'], 'percent': round(x['count']/total_leads*100, 1) if total_leads else 0} for x in source_stats]

    # --- THỐNG KÊ FANPAGE ---
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

    # --- THỐNG KÊ TỈNH THÀNH ---
    city_stats_raw = customers.values('city').annotate(count=Count('id')).order_by('-count')
    city_stats = [{'city': i['city'], 'count': i['count'], 'code': 'None' if not i['city'] else i['city']} for i in city_stats_raw]
    
    # --- THỐNG KÊ GIỚI TÍNH ---
    gender_stats_raw = customers.values('gender').annotate(count=Count('id'))
    gender_data = [{'code': x['gender'], 'label': dict(Customer.Gender.choices).get(x['gender'], 'Không rõ'), 'count': x['count']} for x in gender_stats_raw]

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
        
    # --- THỐNG KÊ SKIN ISSUE ---
    skin_stats_raw = customers.values('skin_condition').annotate(count=Count('id')).order_by('-count')
    skin_data = [{'code': x['skin_condition'], 'label': dict(Customer.SkinIssue.choices).get(x['skin_condition'], 'Không rõ'), 'count': x['count'], 'percent': round(x['count']/total_leads*100, 1) if total_leads else 0} for x in skin_stats_raw]

    # --- CHẤT LƯỢNG DATA ---
    latest_log_subquery = CallLog.objects.filter(customer=OuterRef('pk')).order_by('-call_time').values('status')[:1]
    status_counts_query = customers.annotate(final_status=Subquery(latest_log_subquery)).values('final_status').annotate(total=Count('id'))
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

    # --- HIỆU SUẤT TRÊN DATA MỚI ---
    telesales = User.objects.filter(role='TELESALE')
    logs = CallLog.objects.filter(customer__in=customers.values('pk')) # Logs của data mới
    performance_data = []
    for sale in telesales:
        assigned_count = customers.filter(assigned_telesale=sale).count() 
        sale_logs = logs.filter(caller=sale)
        total_calls = sale_logs.count()
        booked_unique = Appointment.objects.filter(created_at__date__range=[date_start_str, date_end_str], customer__in=customers, customer__assigned_telesale=sale, status='SCHEDULED').values('customer').distinct().count()
        rate_on_assigned = (booked_unique / assigned_count * 100) if assigned_count > 0 else 0
        if assigned_count > 0 or total_calls > 0 or booked_unique > 0:
            performance_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}", 'username': sale.username,
                'assigned': assigned_count, 'total_calls': total_calls, 'booked': booked_unique, 'rate': round(rate_on_assigned, 1)
            })
    performance_data.sort(key=lambda x: x['booked'], reverse=True)

    # =================================================================================
    # PHẦN 2: BÁO CÁO NĂNG SUẤT CHĂM SÓC (RE-CARE) - ĐÂY LÀ PHẦN MỚI
    # Logic: Tính trên toàn bộ hoạt động (Call/Booking) phát sinh trong kỳ, bất kể Data cũ hay mới
    # =================================================================================
    
    recare_data = []
    
    # 1. Lấy tất cả Logs phát sinh trong khoảng thời gian lọc
    period_logs = CallLog.objects.filter(call_time__date__range=[date_start_str, date_end_str])
    
    # 2. Lấy tất cả Lịch hẹn được tạo ra trong khoảng thời gian lọc (Status = SCHEDULED)
    period_bookings = Appointment.objects.filter(
        created_at__date__range=[date_start_str, date_end_str],
        status='SCHEDULED'
    )

    for sale in telesales:
        # Tổng số cuộc gọi Sale thực hiện trong kỳ (Cả cũ và mới)
        my_logs = period_logs.filter(caller=sale)
        total_calls_period = my_logs.count()
        
        # Số khách hàng đã tương tác (Unique)
        total_customers_touched = my_logs.values('customer').distinct().count()
        
        # Số lịch hẹn Sale tạo ra trong kỳ
        # Lưu ý: Dùng created_by để tính công cho người tạo lịch
        my_bookings = period_bookings.filter(created_by=sale).count()
        
        # Tỷ lệ chốt / Số khách đã gọi
        conversion_rate = (my_bookings / total_customers_touched * 100) if total_customers_touched > 0 else 0
        
        # Chỉ hiển thị nếu có hoạt động
        if total_calls_period > 0 or my_bookings > 0:
            recare_data.append({
                'fullname': f"{sale.last_name} {sale.first_name}",
                'username': sale.username,
                'total_calls': total_calls_period,
                'customers_touched': total_customers_touched,
                'booked': my_bookings,
                'rate': round(conversion_rate, 1)
            })
            
    # Sắp xếp theo số lịch hẹn giảm dần
    recare_data.sort(key=lambda x: x['booked'], reverse=True)

    # =================================================================================

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
        'skin_data': skin_data,
        'data_quality_list': data_quality_list,
        'performance_data': performance_data,
        
        # THÊM DỮ LIỆU RE-CARE VÀO CONTEXT
        'recare_data': recare_data, 
        
        'telesales_list': telesales_list,
        'gender_choices': Customer.Gender.choices,
        'fanpage_choices': Customer.Fanpage.choices,
        'skin_choices': Customer.SkinIssue.choices,
        'req_city': req_city,
        'req_gender': req_gender,
        'req_fanpage': req_fanpage,
        'req_telesale': req_telesale,
        'req_skin': req_skin,
    }
    return render(request, 'telesales/report.html', context)