from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from django.contrib.auth import get_user_model
from django.contrib import messages

from apps.customers.models import Customer
from apps.sales.models import Order, Service
from .models import TreatmentSession
from apps.authentication.decorators import allowed_users

User = get_user_model()

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'TECHNICIAN', 'DOCTOR', 'RECEPTIONIST'])
def technician_workspace(request):
    """Giao diện làm việc chính của KTV"""
    doctors = User.objects.filter(role='DOCTOR', is_active=True)
    technicians = User.objects.filter(role='TECHNICIAN', is_active=True)
    
    # Lấy lịch sử làm việc hôm nay của KTV (hoặc toàn bộ nếu là Admin)
    today_sessions = TreatmentSession.objects.select_related('customer', 'service', 'technician').order_by('-session_date')[:20]

    context = {
        'doctors': doctors,
        'technicians': technicians,
        'history': today_sessions
    }
    return render(request, 'service_calendar/dashboard.html', context)

@login_required
def api_search_customer_services(request):
    """API tìm khách và load dịch vụ đã mua"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập SĐT hoặc Mã KH'})

    # Tìm khách hàng
    customers = Customer.objects.filter(Q(phone=query) | Q(customer_code=query))
    
    if not customers.exists():
        return JsonResponse({'success': False, 'message': 'Không tìm thấy khách hàng này.'})
    
    customer = customers.first()
    
    # Lấy các đơn hàng ĐÃ THANH TOÁN của khách
    paid_orders = Order.objects.filter(customer=customer, is_paid=True).select_related('service')
    
    services_data = []
    total_spent = 0
    
    for order in paid_orders:
        if order.service:
            services_data.append({
                'order_id': order.id,
                'service_id': order.service.id,
                'service_name': order.service.name,
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
            order_id = request.POST.get('order_id') # ID đơn hàng chứa dịch vụ
            doctor_id = request.POST.get('doctor_id')
            technician_id = request.POST.get('technician_id')
            note = request.POST.get('note')

            if not customer_id or not order_id or not technician_id:
                messages.error(request, "Thiếu thông tin bắt buộc (Khách, Dịch vụ, KTV).")
                return redirect('service_calendar:dashboard')

            order = Order.objects.get(id=order_id)
            
            TreatmentSession.objects.create(
                customer_id=customer_id,
                order=order,
                service=order.service, # Lấy dịch vụ từ đơn hàng
                doctor_id=doctor_id if doctor_id else None,
                technician_id=technician_id,
                note=note,
                created_by=request.user
            )
            messages.success(request, f"Đã lưu buổi làm: {order.service.name} cho khách {order.customer.name}")
            
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")

    return redirect('service_calendar:dashboard')