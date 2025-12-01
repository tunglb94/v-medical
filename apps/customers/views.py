from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator

from .models import Customer
from .forms import CustomerForm
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.sales.models import Order
from apps.authentication.decorators import allowed_users

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE']) 
def customer_list(request):
    query = request.GET.get('q', '')
    source_filter = request.GET.get('source', '')
    skin_filter = request.GET.get('skin', '')
    city_filter = request.GET.get('city', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    customers = Customer.objects.all().order_by('-created_at')
    
    if query: customers = customers.filter(Q(name__icontains=query) | Q(phone__icontains=query))
    if source_filter: customers = customers.filter(source=source_filter)
    if skin_filter: customers = customers.filter(skin_condition=skin_filter)
    if city_filter: customers = customers.filter(city__icontains=city_filter)
    if date_from and date_to: customers = customers.filter(created_at__date__range=[date_from, date_to])

    source_choices = Customer.Source.choices
    skin_choices = Customer.SkinIssue.choices # <--- QUAY VỀ SkinIssue
    cities = Customer.objects.values_list('city', flat=True).distinct().exclude(city__isnull=True)

    total_count = customers.count()
    paginator = Paginator(customers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj, 'total_count': total_count,
        'query': query, 'source_filter': source_filter, 'skin_filter': skin_filter,
        'city_filter': city_filter, 'date_from': date_from, 'date_to': date_to,
        'source_choices': source_choices, 'skin_choices': skin_choices, 'cities': cities
    }
    return render(request, 'customers/customer_list.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE'])
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    call_logs = CallLog.objects.filter(customer=customer).order_by('-call_time')
    appointments = Appointment.objects.filter(customer=customer).order_by('-appointment_date')
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    total_spent = orders.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    visit_count = appointments.filter(status__in=['ARRIVED', 'COMPLETED']).count()

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ!")
            return redirect('customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)

    context = {
        'customer': customer, 'form': form,
        'call_logs': call_logs, 'appointments': appointments, 'orders': orders,
        'total_spent': total_spent, 'visit_count': visit_count,
    }
    return render(request, 'customers/customer_detail.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, "Đã xóa khách hàng.")
        return redirect('customer_list')
    return redirect('customer_detail', pk=pk)