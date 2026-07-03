from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.authentication.decorators import allowed_users
from apps.customers.models import Customer
from apps.sales.models import Order, Service
from apps.service_calendar.models import TreatmentSession
from django.contrib.auth.decorators import login_required

from .models import PlannedSession

User = get_user_model()

PORTAL_ROLES = ['ADMIN', 'DOCTOR', 'TECHNICIAN']


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def patient_list(request):
    query = request.GET.get('q', '').strip()

    customers = Customer.objects.filter(order__total_amount__gt=0).annotate(
        last_order_date=Max('order__order_date')
    ).distinct().order_by('-last_order_date')

    if query:
        customers = customers.filter(
            Q(name__icontains=query) | Q(phone__icontains=query) | Q(customer_code__icontains=query)
        )

    return render(request, 'clinical_portal/patient_list.html', {
        'customers': customers[:100],
        'query': query,
    })


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def patient_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    orders = Order.objects.filter(customer=customer, total_amount__gt=0).select_related('service').prefetch_related(
        'planned_sessions'
    ).order_by('-order_date')

    services = Service.objects.all().order_by('name')
    doctors = User.objects.filter(role='DOCTOR', is_active=True)
    technicians = User.objects.filter(role='TECHNICIAN', is_active=True)

    orders_data = []
    for order in orders:
        sessions = list(order.planned_sessions.select_related('service', 'assigned_doctor', 'assigned_technician').all())
        orders_data.append({
            'order': order,
            'sessions': sessions,
            'has_plan': len(sessions) > 0,
        })

    return render(request, 'clinical_portal/patient_detail.html', {
        'customer': customer,
        'orders_data': orders_data,
        'services': services,
        'doctors': doctors,
        'technicians': technicians,
    })


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def save_session_plan(request, order_id):
    """Tự sinh buổi chính (nếu chưa có) + thêm buổi tặng kèm theo form gửi lên."""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        if not order.planned_sessions.filter(session_type=PlannedSession.SessionType.MAIN).exists():
            total_main = order.total_sessions or 1
            main_first_date = request.POST.get('main_first_date') or None
            main_doctor_id = request.POST.get('main_doctor_id') or None
            main_technician_id = request.POST.get('main_technician_id') or None
            for i in range(1, total_main + 1):
                is_first = (i == 1 and main_first_date)
                PlannedSession.objects.create(
                    order=order, customer=order.customer, service=order.service,
                    session_type=PlannedSession.SessionType.MAIN,
                    session_number=i, total_in_group=total_main,
                    scheduled_date=main_first_date if is_first else None,
                    status=PlannedSession.Status.SCHEDULED if is_first else PlannedSession.Status.PENDING,
                    assigned_doctor_id=main_doctor_id if is_first else None,
                    assigned_technician_id=main_technician_id if is_first else None,
                    created_by=request.user,
                )

        bonus_service_ids = request.POST.getlist('bonus_service_id')
        bonus_quantities = request.POST.getlist('bonus_quantity')
        bonus_first_dates = request.POST.getlist('bonus_first_date')
        bonus_doctor_ids = request.POST.getlist('bonus_doctor_id')
        bonus_technician_ids = request.POST.getlist('bonus_technician_id')
        for service_id, qty_raw, first_date, doctor_id, technician_id in zip(
            bonus_service_ids, bonus_quantities, bonus_first_dates, bonus_doctor_ids, bonus_technician_ids
        ):
            if not service_id or not qty_raw:
                continue
            try:
                qty = int(qty_raw)
            except ValueError:
                continue
            if qty <= 0:
                continue
            for i in range(1, qty + 1):
                is_first = (i == 1 and first_date)
                PlannedSession.objects.create(
                    order=order, customer=order.customer, service_id=service_id,
                    session_type=PlannedSession.SessionType.BONUS,
                    session_number=i, total_in_group=qty,
                    scheduled_date=first_date if is_first else None,
                    status=PlannedSession.Status.SCHEDULED if is_first else PlannedSession.Status.PENDING,
                    assigned_doctor_id=doctor_id if is_first else None,
                    assigned_technician_id=technician_id if is_first else None,
                    created_by=request.user,
                )

        messages.success(request, "Đã cập nhật kế hoạch điều trị.")

    return redirect('clinical_portal:patient_detail', customer_id=order.customer_id)


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def book_session(request, session_id):
    session = get_object_or_404(PlannedSession, id=session_id)
    doctors = User.objects.filter(role='DOCTOR', is_active=True)
    technicians = User.objects.filter(role='TECHNICIAN', is_active=True)

    if request.method == 'POST':
        scheduled_date = request.POST.get('scheduled_date')
        doctor_id = request.POST.get('assigned_doctor')
        technician_id = request.POST.get('assigned_technician')

        if scheduled_date:
            session.scheduled_date = scheduled_date
            session.assigned_doctor_id = doctor_id or None
            session.assigned_technician_id = technician_id or None
            session.status = PlannedSession.Status.SCHEDULED
            session.save()
            messages.success(request, "Đã đặt lịch buổi hẹn.")
        else:
            messages.error(request, "Vui lòng chọn ngày giờ hẹn.")

        return redirect('clinical_portal:patient_detail', customer_id=session.customer_id)

    return render(request, 'clinical_portal/book_session.html', {
        'session': session,
        'doctors': doctors,
        'technicians': technicians,
    })


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def complete_session(request, session_id):
    session = get_object_or_404(PlannedSession, id=session_id)

    if request.method == 'POST':
        log = TreatmentSession.objects.create(
            customer=session.customer,
            service=session.service,
            order=session.order,
            technician=session.assigned_technician,
            doctor=session.assigned_doctor,
            note=session.note,
            created_by=request.user,
        )
        session.status = PlannedSession.Status.DONE
        session.completed_log = log
        session.save()
        messages.success(request, "Đã đánh dấu hoàn thành buổi điều trị.")

    return redirect('clinical_portal:patient_detail', customer_id=session.customer_id)


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def cancel_session(request, session_id):
    session = get_object_or_404(PlannedSession, id=session_id)

    if request.method == 'POST':
        session.status = PlannedSession.Status.CANCELLED
        session.save()
        messages.success(request, "Đã huỷ buổi hẹn.")

    return redirect('clinical_portal:patient_detail', customer_id=session.customer_id)


@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=PORTAL_ROLES)
def my_schedule(request):
    sessions = PlannedSession.objects.filter(
        status=PlannedSession.Status.SCHEDULED
    ).filter(
        Q(assigned_doctor=request.user) | Q(assigned_technician=request.user)
    ).select_related('customer', 'service', 'order', 'assigned_doctor', 'assigned_technician').order_by('scheduled_date')

    today = timezone.now().date()

    return render(request, 'clinical_portal/my_schedule.html', {
        'sessions': sessions,
        'today': today,
    })
