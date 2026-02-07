from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Max
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta # [THÊM] Import datetime

from apps.customers.models import Customer
from apps.sales.models import Order, Service
from .models import TreatmentSession
from apps.authentication.decorators import allowed_users

User = get_user_model()

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TECHNICIAN', 'DOCTOR', 'RECEPTIONIST'])
def technician_workspace(request):
    """Giao diện làm việc chính của KTV & Bảng Xếp Hạng"""
    
    # --- 1. XỬ LÝ BỘ LỌC NGÀY THÁNG & KTV ---
    today = timezone.now().date()
    
    # Lấy tham số từ URL (nếu không có thì mặc định là đầu tháng -> hôm nay)
    date_start_str = request.GET.get('date_start')
    date_end_str = request.GET.get('date_end')
    filter_tech_id = request.GET.get('filter_tech_id')

    if date_start_str:
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d').date()
    else:
        date_start = today.replace(day=1) # Mặc định ngày mùng 1

    if date_end_str:
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d').date()
    else:
        date_end = today # Mặc định hôm nay

    # --- 2. LẤY DỮ LIỆU CƠ BẢN ---
    doctors = User.objects.filter(role='DOCTOR', is_active=True)
    technicians = User.objects.filter(role='TECHNICIAN', is_active=True)
    
    # Khách hàng active (để hiển thị bên trái)
    active_customers = Customer.objects.filter(
        order__total_amount__gt=0
    ).annotate(
        last_order_date=Max('order__order_date')
    ).order_by('-last_order_date').distinct()[:50]

    # --- 3. TRUY VẤN LỊCH SỬ & LEADERBOARD THEO BỘ LỌC ---
    
    # Query cơ bản: Lọc theo ngày
    # Lưu ý: __date__range lọc theo ngày (bỏ qua giờ phút)
    base_qs = TreatmentSession.objects.filter(
        session_date__date__range=(date_start, date_end)
    ).select_related('customer', 'service', 'technician', 'order', 'doctor')

    # A. BẢNG LỊCH SỬ (HISTORY)
    # Nếu có chọn KTV cụ thể thì lọc thêm, nếu không thì hiện hết
    history_qs = base_qs.order_by('-session_date')
    if filter_tech_id and filter_tech_id != 'all':
        history_qs = history_qs.filter(technician_id=filter_tech_id)
    
    # B. BẢNG XẾP HẠNG (LEADERBOARD)
    # Bảng xếp hạng luôn tính TOÀN BỘ KTV trong khoảng thời gian đó để so sánh
    # (Không bị ảnh hưởng bởi filter_tech_id để đảm bảo tính công bằng)
    tech_stats = {}

    for session in base_qs:
        if not session.technician:
            continue
            
        tech = session.technician
        tech_id = tech.id
        
        if tech_id not in tech_stats:
            tech_stats[tech_id] = {
                'name': f"{tech.last_name} {tech.first_name}",
                'username': tech.username,
                'count': 0,
                'total_money': 0
            }

        # Tính tiền
        if session.order:
            price_base = session.order.total_amount
            total_sessions = session.order.total_sessions if session.order.total_sessions > 0 else 1
        else:
            price_base = session.service.base_price
            total_sessions = 1
        
        rate = session.service.commission_rate
        full_commission = float(price_base) * (float(rate) / 100)
        money_per_session = full_commission / total_sessions

        tech_stats[tech_id]['count'] += 1
        tech_stats[tech_id]['total_money'] += money_per_session

    leaderboard = list(tech_stats.values())
    leaderboard.sort(key=lambda x: x['total_money'], reverse=True)

    context = {
        'doctors': doctors,
        'technicians': technicians,
        'active_customers': active_customers,
        
        # Dữ liệu hiển thị
        'history': history_qs,
        'leaderboard': leaderboard,
        
        # Giá trị bộ lọc để điền lại vào form
        'date_start': date_start.strftime('%Y-%m-%d'),
        'date_end': date_end.strftime('%Y-%m-%d'),
        'filter_tech_id': int(filter_tech_id) if filter_tech_id and filter_tech_id != 'all' else None
    }
    return render(request, 'service_calendar/dashboard.html', context)

# ... (Giữ nguyên các hàm api_search..., create..., edit..., delete...) ...
@login_required
def api_search_customer_services(request):
    """API tìm khách và load dịch vụ đã mua"""
    query = request.GET.get('q', '').strip()
    if not query:
        customer_id = request.GET.get('id')
        if customer_id:
            customers = Customer.objects.filter(id=customer_id)
        else:
            return JsonResponse({'success': False, 'message': 'Vui lòng nhập thông tin'})
    else:
        customers = Customer.objects.filter(Q(phone=query) | Q(customer_code=query))
    
    if not customers.exists():
        return JsonResponse({'success': False, 'message': 'Không tìm thấy khách hàng này.'})
    
    customer = customers.first()
    
    paid_orders = Order.objects.filter(
        customer=customer, 
        total_amount__gt=0
    ).select_related('service').order_by('-order_date')
    
    services_data = []
    total_spent = 0
    
    for order in paid_orders:
        if order.service:
            status_text = "Đủ" if order.is_paid else "Nợ"
            services_data.append({
                'order_id': order.id,
                'service_id': order.service.id,
                'service_name': f"{order.service.name} ({status_text})",
                'price': order.total_amount,
                'date': order.order_date.strftime('%d/%m/%Y'),
                'total_sessions': order.total_sessions
            })
            total_spent += order.total_amount

    return JsonResponse({
        'success': True,
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'code': customer.customer_code,
            'total_spent': total_spent
        },
        'services': services_data
    })


@login_required
def create_treatment_session(request):
    """Lưu buổi làm dịch vụ & Cập nhật số buổi"""
    if request.method == 'POST':
        try:
            customer_id = request.POST.get('customer_id')
            order_id = request.POST.get('order_id')
            doctor_id = request.POST.get('doctor_id')
            technician_id = request.POST.get('technician_id')
            note = request.POST.get('note')
            total_sessions_input = request.POST.get('total_sessions')

            if not customer_id or not order_id or not technician_id:
                messages.error(request, "Thiếu thông tin bắt buộc (Khách, Dịch vụ, KTV).")
                return redirect('service_calendar:dashboard')

            order = Order.objects.get(id=order_id)
            
            if total_sessions_input:
                try:
                    ts = int(total_sessions_input)
                    if ts > 0:
                        order.total_sessions = ts
                        order.save()
                except ValueError:
                    pass 

            TreatmentSession.objects.create(
                customer_id=customer_id,
                order=order,
                service=order.service,
                doctor_id=doctor_id if doctor_id else None,
                technician_id=technician_id,
                note=note,
                created_by=request.user
            )
            messages.success(request, f"Đã lưu buổi làm & cập nhật liệu trình {order.total_sessions} buổi.")
            
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")

    return redirect('service_calendar:dashboard')


@login_required
def edit_treatment_session(request):
    """Sửa thông tin buổi làm việc"""
    if request.method == 'POST':
        try:
            session_id = request.POST.get('session_id')
            technician_id = request.POST.get('technician_id')
            doctor_id = request.POST.get('doctor_id')
            note = request.POST.get('note')

            session = TreatmentSession.objects.get(id=session_id)
            
            if technician_id:
                session.technician_id = technician_id
            
            if doctor_id:
                session.doctor_id = doctor_id
            else:
                session.doctor = None 

            session.note = note
            session.save()
            messages.success(request, f"Đã cập nhật buổi làm của khách {session.customer.name}")
            
        except TreatmentSession.DoesNotExist:
            messages.error(request, "Không tìm thấy dữ liệu.")
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")
            
    return redirect('service_calendar:dashboard')


@login_required
def delete_treatment_session(request, session_id):
    """Xóa buổi làm việc"""
    try:
        session = TreatmentSession.objects.get(id=session_id)
        customer_name = session.customer.name
        session.delete()
        messages.success(request, f"Đã xóa buổi làm của khách {customer_name}")
    except TreatmentSession.DoesNotExist:
        messages.error(request, "Không tìm thấy dữ liệu để xóa.")
    
    return redirect('service_calendar:dashboard')