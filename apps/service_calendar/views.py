from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Max
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone

from apps.customers.models import Customer
from apps.sales.models import Order, Service
from .models import TreatmentSession
from apps.authentication.decorators import allowed_users

User = get_user_model()

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TECHNICIAN', 'DOCTOR', 'RECEPTIONIST'])
def technician_workspace(request):
    """Giao diện làm việc chính của KTV & Xem Hoa hồng cá nhân"""
    doctors = User.objects.filter(role='DOCTOR', is_active=True)
    technicians = User.objects.filter(role='TECHNICIAN', is_active=True)
    
    # 1. Lấy lịch sử làm việc TOÀN BỘ hôm nay
    today_sessions = TreatmentSession.objects.select_related('customer', 'service', 'technician').order_by('-session_date')[:20]

    # 2. Lấy danh sách khách hàng CÓ LIỆU TRÌNH
    active_customers = Customer.objects.filter(
        order__total_amount__gt=0
    ).annotate(
        last_order_date=Max('order__order_date')
    ).order_by('-last_order_date').distinct()[:50]

    # 3. TÍNH HOA HỒNG CÁ NHÂN
    today = timezone.now()
    current_month = today.month
    current_year = today.year

    my_sessions_qs = TreatmentSession.objects.filter(
        technician=request.user,
        session_date__month=current_month,
        session_date__year=current_year
    ).select_related('order', 'service', 'customer').order_by('-session_date')

    my_commissions = []
    total_commission_month = 0

    for session in my_sessions_qs:
        # Lấy giá trị và số buổi từ Order
        if session.order:
            price_base = session.order.total_amount
            # [MỚI] Lấy số buổi từ đơn hàng
            total_sessions = session.order.total_sessions if session.order.total_sessions > 0 else 1
        else:
            price_base = session.service.base_price
            total_sessions = 1
        
        rate = session.service.commission_rate
        
        # [CÔNG THỨC MỚI] (Giá * % / 100) / Tổng số buổi
        full_commission = float(price_base) * (float(rate) / 100)
        money_per_session = full_commission / total_sessions
        
        my_commissions.append({
            'id': session.id,
            'date': session.session_date,
            'customer': session.customer.name,
            'service': f"{session.service.name} (Gói {total_sessions}b)", # Hiển thị số buổi
            'price': price_base,
            'rate': rate,
            'money': money_per_session
        })
        total_commission_month += money_per_session

    context = {
        'doctors': doctors,
        'technicians': technicians,
        'history': today_sessions,
        'active_customers': active_customers,
        'my_commissions': my_commissions,
        'total_commission_month': total_commission_month,
        'current_month': current_month
    }
    return render(request, 'service_calendar/dashboard.html', context)


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
                # [MỚI] Trả về số buổi hiện tại của đơn hàng
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
            
            # [MỚI] Lấy số buổi từ form gửi lên
            total_sessions_input = request.POST.get('total_sessions')

            if not customer_id or not order_id or not technician_id:
                messages.error(request, "Thiếu thông tin bắt buộc (Khách, Dịch vụ, KTV).")
                return redirect('service_calendar:dashboard')

            order = Order.objects.get(id=order_id)
            
            # [MỚI] Cập nhật số buổi vào Order nếu có thay đổi
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