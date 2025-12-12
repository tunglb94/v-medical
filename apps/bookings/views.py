from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Subquery, OuterRef, Count
from django.utils import timezone
from datetime import timedelta, date

from .models import Appointment
from apps.customers.models import Customer
from apps.sales.models import Service 
from apps.authentication.decorators import allowed_users

User = get_user_model()

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['RECEPTION', 'ADMIN'])
def reception_dashboard(request):
    today = timezone.now().date()
    
    # --- FIX: Đã xóa filter(is_active=True) vì trường này không còn tồn tại ---
    services = Service.objects.order_by('name')
    # -------------------------------------------------------------------------
    
    appointments = Appointment.objects.filter(
        appointment_date__date=today
    ).order_by('appointment_date')
    
    # Filter for the table (e.g., scheduled, arrived, completed)
    status_filter = request.GET.get('status', 'SCHEDULED')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
        
    # Handling POST for check-in/status update
    if request.method == 'POST':
        app_id = request.POST.get('appointment_id')
        new_status = request.POST.get('new_status')
        
        appointment = get_object_or_404(Appointment, id=app_id)
        appointment.status = new_status
        appointment.save()
        messages.success(request, f"Cập nhật trạng thái hẹn cho {appointment.customer.name} thành {appointment.get_status_display}.")
        return redirect('reception_dashboard')

    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_choices': Appointment.Status.choices,
        'services': services,
    }
    return render(request, 'bookings/reception_dashboard.html', context)