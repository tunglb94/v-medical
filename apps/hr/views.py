from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import datetime

from .models import Attendance, SalarySlip, EmployeeContract
from apps.sales.models import Order # Import để lấy doanh số
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- 1. CHẤM CÔNG THỦ CÔNG (ADMIN TÍCH CHỌN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def attendance_list(request):
    # Lấy ngày từ GET request hoặc mặc định là hôm nay
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()

    # Xử lý lưu điểm danh khi bấm nút LƯU
    if request.method == 'POST':
        # Lấy danh sách ID nhân viên được tích chọn
        present_user_ids = request.POST.getlist('user_ids')
        
        # Xóa dữ liệu cũ của ngày hôm đó để cập nhật lại (tránh trùng lặp)
        Attendance.objects.filter(date=selected_date).delete()
        
        # Tạo bản ghi mới cho những người được tích
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

    # Lấy danh sách tất cả nhân viên (trừ Admin tổng nếu muốn)
    users = User.objects.filter(is_active=True).exclude(is_superuser=True).order_by('first_name')
    
    # Lấy danh sách những người đã được điểm danh ngày hôm đó
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
    
    if not selected_month_str: selected_month_str = today.strftime('%Y-%m')

    try:
        selected_date = datetime.strptime(selected_month_str, '%Y-%m').date()
    except ValueError:
        selected_date = today

    if request.method == 'POST':
        # Lấy tất cả nhân viên có cấu hình lương
        contracts = EmployeeContract.objects.select_related('user').all()
        count = 0
        
        for contract in contracts:
            user = contract.user
            
            # 1. Tính số công thực tế (Đếm số bản ghi Attendance trong tháng)
            actual_work_days = Attendance.objects.filter(
                user=user, 
                date__year=selected_date.year, 
                date__month=selected_date.month
            ).count()

            # 2. Tính lương cứng theo công
            standard_days = 26 # Công chuẩn
            # Lương theo ngày = Lương cứng / 26
            salary_by_days = (contract.base_salary / standard_days) * actual_work_days

            # 3. Tính doanh số bán hàng trong tháng (Dựa vào Order)
            # Giả sử trường 'sale_consultant' trong Order là người được tính doanh số
            monthly_revenue = Order.objects.filter(
                sale_consultant=user,
                created_at__year=selected_date.year,
                created_at__month=selected_date.month
                # Có thể thêm điều kiện: is_paid=True nếu chỉ tính đơn đã thanh toán
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            # 4. Tính hoa hồng
            commission_amt = monthly_revenue * (contract.commission_rate / 100)

            # 5. Tổng lương
            total_salary = salary_by_days + contract.allowance + commission_amt

            # Lưu vào Database
            slip, created = SalarySlip.objects.get_or_create(
                user=user,
                month=selected_date.replace(day=1),
                defaults={'base_salary_lock': contract.base_salary}
            )
            
            # Cập nhật các chỉ số
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