from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model 

from .models import Customer
from .forms import CustomerForm
from apps.telesales.models import CallLog
from apps.bookings.models import Appointment
from apps.sales.models import Order
from apps.authentication.decorators import allowed_users

User = get_user_model() 

# --- 1. HÀM THÊM KHÁCH HÀNG & CHIA SỐ TỰ ĐỘNG ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE', 'MARKETING'])
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            
            # === LOGIC CHIA SỐ CÔNG BẰNG (LOAD BALANCING) ===
            # Nếu người nhập là Telesale thuộc TEAM A
            if request.user.role == 'TELESALE' and request.user.team == 'TEAM_A':
                
                # 1. Tìm các thành viên Team B đang hoạt động
                team_b_members = User.objects.filter(
                    role='TELESALE',
                    team='TEAM_B',
                    is_active=True
                )
                
                if team_b_members.exists():
                    # 2. Thuật toán: Chia cho người ít việc nhất, nếu bằng nhau thì random
                    # Lưu ý: Do model không có related_name, Django mặc định là 'customer_set'
                    target_telesale = team_b_members.annotate(
                        load=Count('customer_set') 
                    ).order_by('load', '?').first()
                    
                    # 3. Gán số
                    if target_telesale:
                        customer.assigned_telesale = target_telesale
                        messages.info(request, f"🚀 Data đã được chuyển tự động cho: {target_telesale.last_name} {target_telesale.first_name} (Team B)")
            
            customer.save()
            messages.success(request, "Thêm khách hàng thành công!")
            return redirect('customer_list')
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'title': 'Thêm Khách Hàng Mới'
    }
    return render(request, 'customers/customer_form.html', context)

# --- 2. DANH SÁCH KHÁCH HÀNG ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER', 'TECHNICIAN']) 
def customer_list(request):
    query = request.GET.get('q', '')
    source_filter = request.GET.get('source', '')
    skin_filter = request.GET.get('skin', '')
    city_filter = request.GET.get('city', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    customers = Customer.objects.all().order_by('-created_at')
    
    # --- PHÂN QUYỀN TEAM ---
    if request.user.role == 'TELESALE' and request.user.team:
        teammate_ids = User.objects.filter(team=request.user.team).values_list('id', flat=True)
        customers = customers.filter(
            Q(assigned_telesale_id__in=teammate_ids) | Q(assigned_telesale__isnull=True)
        )

    # --- TÌM KIẾM ---
    if query: 
        customers = customers.filter(
            Q(name__icontains=query) | 
            Q(phone__icontains=query) | 
            Q(customer_code__icontains=query)
        )
    
    if source_filter: customers = customers.filter(source=source_filter)
    if skin_filter: customers = customers.filter(skin_condition=skin_filter)
    if city_filter: customers = customers.filter(city__icontains=city_filter)
    if date_from and date_to: customers = customers.filter(created_at__date__range=[date_from, date_to])

    source_choices = Customer.Source.choices
    skin_choices = Customer.SkinIssue.choices
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

# --- 3. CHI TIẾT KHÁCH HÀNG ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST', 'TELESALE', 'MARKETING', 'CONTENT', 'EDITOR', 'DESIGNER', 'TECHNICIAN'])
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    call_logs = CallLog.objects.filter(customer=customer).order_by('-call_time')
    appointments = Appointment.objects.filter(customer=customer).order_by('-appointment_date')
    
    orders = Order.objects.filter(customer=customer).order_by('-order_date')
    
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

# --- 4. XÓA KHÁCH HÀNG ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, "Đã xóa khách hàng.")
        return redirect('customer_list')
    return redirect('customer_detail', pk=pk)