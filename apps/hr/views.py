from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import datetime

from .models import Attendance, SalarySlip, EmployeeContract
from apps.sales.models import Order
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- 1. CHẤM CÔNG THỦ CÔNG (ADMIN TÍCH CHỌN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def attendance_list(request):
    # Lấy ngày từ GET request hoặc mặc định là hôm nay
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Xử lý khi Admin bấm nút LƯU ĐIỂM DANH
    if request.method == 'POST':
        present_user_ids = request.POST.getlist('user_ids')
        
        # Xóa điểm danh cũ của ngày đó để tránh trùng lặp
        Attendance.objects.filter(date=selected_date).delete()
        
        # Tạo danh sách điểm danh mới
        new_attendances = []
        for uid in present_user_ids:
            new_attendances.append(Attendance(
                user_id=uid,
                date=selected_date,
                is_present=True
            ))
        Attendance.objects.bulk_create(new_attendances)
        
        messages.success(request, f"Đã lưu điểm danh ngày {selected_date.strftime('%d/%m/%Y')}")
        return redirect(f'/hr/attendance/?date={selected_date}')

    # Lấy danh sách nhân viên để hiển thị bảng
    users = User.objects.filter(is_active=True).exclude(is_superuser=True).order_by('first_name')
    
    # Lấy danh sách những người ĐÃ ĐƯỢC điểm danh (để check sẵn vào ô)
    present_ids = Attendance.objects.filter(date=selected_date).values_list('user_id', flat=True)

    context = {
        'users': users,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'present_ids': list(present_ids)
    }
    return render(request, 'hr/attendance_list.html', context)


# --- 2. QUẢN LÝ LƯƠNG (TÍNH TỰ ĐỘNG LƯƠNG CỨNG + HOA HỒNG) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def payroll_dashboard(request):
    today = timezone.now().date()
    selected_month_str = request.GET.get('month', today.strftime('%Y-%m'))
    
    if not selected_month_str: 
        selected_month_str = today.strftime('%Y-%m')

    try:
        selected_date = datetime.strptime(selected_month_str, '%Y-%m').date()
    except ValueError:
        selected_date = today

    if request.method == 'POST':
        # Lấy danh sách hợp đồng để tính lương
        contracts = EmployeeContract.objects.select_related('user').all()
        count = 0
        
        for contract in contracts:
            user = contract.user
            
            # 1. Đếm số ngày công thực tế trong tháng
            actual_work_days = Attendance.objects.filter(
                user=user, 
                date__year=selected_date.year, 
                date__month=selected_date.month,
                is_present=True
            ).count()

            # 2. Tính lương cứng (Công thức: Lương cứng / 26 * số ngày làm)
            standard_days = 26
            salary_by_days = (contract.base_salary / standard_days) * actual_work_days

            # 3. Tính doanh số bán hàng (chỉ tính đơn trong tháng này)
            monthly_revenue = Order.objects.filter(
                sale_consultant=user,
                created_at__year=selected_date.year,
                created_at__month=selected_date.month
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            # 4. Tính hoa hồng
            commission_amt = monthly_revenue * (contract.commission_rate / 100)

            # 5. Tổng thực lĩnh
            total_salary = salary_by_days + contract.allowance + commission_amt

            # Lưu vào Database (Tạo mới hoặc Cập nhật)
            slip, created = SalarySlip.objects.get_or_create(
                user=user,
                month=selected_date.replace(day=1),
                defaults={'base_salary_lock': contract.base_salary}
            )
            
            # Cập nhật số liệu mới nhất
            slip.standard_work_days = standard_days
            slip.actual_work_days = actual_work_days
            slip.base_salary_lock = contract.base_salary
            slip.allowance_lock = contract.allowance
            
            slip.sales_revenue = monthly_revenue
            slip.commission_rate_lock = contract.commission_rate
            slip.commission_amount = commission_amt
            
            slip.total_salary = total_salary + slip.bonus - slip.deduction
            slip.save()
            count += 1
        
        messages.success(request, f"Đã tính lương cho {count} nhân viên.")
        return redirect(f'/hr/payroll/?month={selected_month_str}')

    slips = SalarySlip.objects.filter(month__year=selected_date.year, month__month=selected_date.month)
    total_payout = sum(slip.total_salary for slip in slips)

    context = {
        'slips': slips,
        'selected_month': selected_month_str,
        'total_payout': total_payout
    }
    return render(request, 'hr/payroll_dashboard.html', context)


# --- 3. QUẢN LÝ HỢP ĐỒNG (ĐÂY LÀ PHẦN BẠN ĐANG THIẾU) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def contract_management(request):
    # Xử lý khi Admin bấm nút LƯU trong popup thêm/sửa
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        base_salary = request.POST.get('base_salary', 0)
        allowance = request.POST.get('allowance', 0)
        commission_rate = request.POST.get('commission_rate', 0)
        start_date = request.POST.get('start_date')

        try:
            target_user = User.objects.get(id=user_id)
            # Tạo mới hoặc Cập nhật nếu đã có
            EmployeeContract.objects.update_or_create(
                user=target_user,
                defaults={
                    'base_salary': base_salary,
                    'allowance': allowance,
                    'commission_rate': commission_rate,
                    'start_date': start_date if start_date else timezone.now().date()
                }
            )
            messages.success(request, f"Đã lưu cấu hình lương cho: {target_user.username}")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
        
        return redirect('contract_management')

    # Lấy dữ liệu hiển thị ra bảng
    contracts = EmployeeContract.objects.select_related('user').all()
    
    # Lấy danh sách nhân viên chưa có hợp đồng (để hiện trong dropdown thêm mới)
    existing_ids = contracts.values_list('user_id', flat=True)
    users_without_contract = User.objects.exclude(id__in=existing_ids).exclude(is_superuser=True)
    
    context = {
        'contracts': contracts,
        'users_without_contract': users_without_contract,
    }
    return render(request, 'hr/contract_list.html', context)