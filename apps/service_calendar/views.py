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
    # [SỬA LẠI]: Thay is_paid=True thành total_amount__gt=0 (Có đơn hàng giá trị > 0 là hiện)
    active_customers = Customer.objects.filter(
        order__total_amount__gt=0  # <--- SỬA TẠI ĐÂY
    ).annotate(
        last_order_date=Max('order__order_date')
    ).order_by('-last_order_date').distinct()[:50]

    # 3. Tính hoa hồng cá nhân
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
        price_base = session.order.total_amount if session.order else session.service.base_price
        rate = session.service.commission_rate
        money = float(price_base) * (float(rate) / 100)
        
        my_commissions.append({
            'date': session.session_date,
            'customer': session.customer.name,
            'service': session.service.name,
            'price': price_base,
            'rate': rate,
            'money': money
        })
        total_commission_month += money

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
    
    # [SỬA LẠI]: Lấy tất cả đơn có tiền (bao gồm cả nợ), không bắt buộc is_paid=True
    paid_orders = Order.objects.filter(
        customer=customer, 
        total_amount__gt=0 # <--- SỬA TẠI ĐÂY
    ).select_related('service').order_by('-order_date')
    
    services_data = []
    total_spent = 0
    
    for order in paid_orders:
        if order.service:
            # Tính trạng thái thanh toán để hiển thị cho KTV biết
            status_text = "Đủ" if order.is_paid else "Nợ"
            
            services_data.append({
                'order_id': order.id,
                'service_id': order.service.id,
                'service_name': f"{order.service.name} ({status_text})", # Thêm chữ (Nợ) nếu chưa trả hết
                'price': order.total_amount,
                'date': order.order_date.strftime('%d/%m/%Y')
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
    """Lưu buổi làm dịch vụ"""
    if request.method == 'POST':
        try:
            customer_id = request.POST.get('customer_id')
            order_id = request.POST.get('order_id')
            doctor_id = request.POST.get('doctor_id')
            technician_id = request.POST.get('technician_id')
            note = request.POST.get('note')

            if not customer_id or not order_id or not technician_id:
                messages.error(request, "Thiếu thông tin bắt buộc.")
                return redirect('service_calendar:dashboard')

            order = Order.objects.get(id=order_id)
            
            TreatmentSession.objects.create(
                customer_id=customer_id,
                order=order,
                service=order.service,
                doctor_id=doctor_id if doctor_id else None,
                technician_id=technician_id,
                note=note,
                created_by=request.user
            )
            messages.success(request, f"Đã lưu buổi làm thành công!")
            
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")

    return redirect('service_calendar:dashboard')