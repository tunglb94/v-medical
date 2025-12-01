from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime

from .models import Attendance, SalarySlip, EmployeeContract
from apps.authentication.decorators import allowed_users

User = get_user_model()

# --- 1. XỬ LÝ CHẤM CÔNG (Check-in / Check-out) ---
@login_required(login_url='/auth/login/')
def toggle_attendance(request):
    today = timezone.now().date()
    user = request.user
    
    attendance = Attendance.objects.filter(user=user, date=today).first()

    if not attendance:
        Attendance.objects.create(
            user=user,
            date=today,
            check_in=timezone.now().time(),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Xin chào {user.last_name}! Đã Check-in thành công.")
    else:
        if not attendance.check_out:
            attendance.check_out = timezone.now().time()
            attendance.save()
            messages.success(request, f"Tạm biệt {user.last_name}! Đã Check-out thành công.")
        else:
            messages.warning(request, "Bạn đã hoàn thành chấm công hôm nay rồi.")
    
    return redirect('attendance_list')

# --- 2. DANH SÁCH CHẤM CÔNG (ĐÃ SỬA LỖI VALUE ERROR) ---
@login_required(login_url='/auth/login/')
def attendance_list(request):
    today = timezone.now()
    
    # Lấy tham số từ URL, nếu rỗng thì lấy mặc định
    month_val = request.GET.get('month')
    year_val = request.GET.get('year')

    # Xử lý an toàn: Chuyển sang int, nếu lỗi (do rỗng) thì dùng ngày hiện tại
    try:
        month = int(month_val) if month_val else today.month
        year = int(year_val) if year_val else today.year
    except ValueError:
        month = today.month
        year = today.year

    # Lọc dữ liệu
    attendances = Attendance.objects.filter(date__month=month, date__year=year)

    if request.user.role != 'ADMIN':
        attendances = attendances.filter(user=request.user)
    
    attendances = attendances.order_by('-date')

    context = {
        'attendances': attendances,
        'month': month,
        'year': year
    }
    return render(request, 'hr/attendance_list.html', context)

# --- 3. QUẢN LÝ LƯƠNG (ADMIN) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN'])
def payroll_dashboard(request):
    today = timezone.now().date()
    selected_month_str = request.GET.get('month', today.strftime('%Y-%m'))
    
    # Xử lý an toàn cho tháng lương (phòng trường hợp chuỗi rỗng)
    if not selected_month_str: 
        selected_month_str = today.strftime('%Y-%m')

    try:
        selected_date = datetime.strptime(selected_month_str, '%Y-%m').date()
    except ValueError:
        selected_date = today
        selected_month_str = today.strftime('%Y-%m')

    if request.method == 'POST':
        contracts = EmployeeContract.objects.select_related('user').all()
        count = 0
        
        for contract in contracts:
            user = contract.user
            actual_work_days = Attendance.objects.filter(
                user=user, 
                date__year=selected_date.year, 
                date__month=selected_date.month,
                check_in__isnull=False,
                check_out__isnull=False
            ).count()

            standard_days = 26
            daily_wage = contract.base_salary / standard_days
            total_salary = (daily_wage * actual_work_days) + contract.allowance

            slip, created = SalarySlip.objects.get_or_create(
                user=user,
                month=selected_date.replace(day=1),
                defaults={
                    'base_salary_lock': contract.base_salary,
                    'allowance_lock': contract.allowance,
                    'standard_work_days': standard_days,
                }
            )
            
            slip.actual_work_days = actual_work_days
            slip.total_salary = total_salary + slip.bonus - slip.deduction
            slip.save()
            count += 1
        
        messages.success(request, f"Đã tính lương cho {count} nhân viên tháng {selected_date.month}/{selected_date.year}")
        return redirect(f'/hr/payroll/?month={selected_month_str}')

    slips = SalarySlip.objects.filter(month__year=selected_date.year, month__month=selected_date.month)
    total_payout = sum(slip.total_salary for slip in slips)

    context = {
        'slips': slips,
        'selected_month': selected_month_str,
        'total_payout': total_payout
    }
    return render(request, 'hr/payroll_dashboard.html', context)