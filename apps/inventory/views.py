from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q, Sum, F, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd # Cần cài đặt: pip install pandas openpyxl

from apps.authentication.decorators import allowed_users
from .models import Product, InventoryLog

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_list(request):
    # --- 1. LỌC VÀ TÌM KIẾM ---
    products = Product.objects.all().order_by('name')
    
    # Tìm kiếm từ khóa
    q = request.GET.get('q')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(code__icontains=q))

    # Lọc theo trạng thái
    status_filter = request.GET.get('status')
    if status_filter == 'out_of_stock':
        products = products.filter(stock=0)
    elif status_filter == 'low_stock':
        products = products.filter(stock__lte=F('min_stock'), stock__gt=0)
    elif status_filter == 'in_stock':
        products = products.filter(stock__gt=F('min_stock'))

    # Đếm số lượng để hiển thị badge
    total_count = Product.objects.count()
    low_stock_count = Product.objects.filter(stock__lte=F('min_stock')).count()

    # --- 2. XỬ LÝ THÊM MỚI NHANH (Chỉ cần Tên) ---
    if request.method == 'POST':
        if 'add_product' in request.POST:
            name = request.POST.get('name')
            # Các trường khác tự động điền mặc định nếu không nhập
            unit = request.POST.get('unit') or 'Hộp' 
            min_stock = request.POST.get('min_stock') or 10
            
            try:
                Product.objects.create(name=name, unit=unit, min_stock=min_stock)
                messages.success(request, f"Đã thêm: {name}")
            except Exception as e:
                messages.error(request, f"Lỗi: {str(e)}")
            return redirect('inventory_list')
            
        # Xử lý Import Excel
        if 'import_file' in request.FILES:
            excel_file = request.FILES['import_file']
            try:
                df = pd.read_excel(excel_file)
                # Giả sử file excel có cột: 'Ten', 'DonVi', 'TonDau'
                count = 0
                for index, row in df.iterrows():
                    name = str(row.get('Ten', '')).strip()
                    if name:
                        unit = str(row.get('DonVi', 'Hộp')).strip()
                        stock = int(row.get('TonDau', 0))
                        
                        # Tạo hoặc cập nhật (nếu trùng tên)
                        obj, created = Product.objects.get_or_create(
                            name=name,
                            defaults={'unit': unit, 'stock': stock}
                        )
                        count += 1
                messages.success(request, f"Đã nhập thành công {count} sản phẩm từ Excel!")
            except Exception as e:
                messages.error(request, f"Lỗi đọc file: {str(e)}")
            return redirect('inventory_list')

    context = {
        'products': products,
        'low_stock_count': low_stock_count,
        'total_count': total_count,
        'current_filter': status_filter,
        'search_query': q
    }
    return render(request, 'inventory/inventory_list.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_transaction(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        trans_type = request.POST.get('type')
        qty_str = request.POST.get('quantity', '0')
        note = request.POST.get('note', '')

        try:
            qty = int(qty_str)
        except ValueError:
            qty = 0

        if qty <= 0:
            messages.error(request, "Số lượng phải lớn hơn 0")
            return redirect('inventory_list')

        if trans_type == 'EXPORT':
            if product.stock < qty:
                messages.error(request, f"Kho không đủ! Hiện còn {product.stock} {product.unit}")
                return redirect('inventory_list')
            product.stock -= qty
            final_qty = -qty
        else: # IMPORT
            product.stock += qty
            final_qty = qty

        product.save()

        InventoryLog.objects.create(
            product=product, change_type=trans_type, quantity=final_qty,
            stock_after=product.stock, user=request.user, note=note
        )
        messages.success(request, "Giao dịch thành công!")
        
    return redirect('inventory_list')

# --- 3. BÁO CÁO XUẤT NHẬP TỒN (Tính toán tự động) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_report(request):
    today = timezone.now()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # Xác định ngày đầu tháng và ngày đầu tháng sau
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Lấy toàn bộ sản phẩm
    products = Product.objects.all().order_by('name')
    report_data = []

    for p in products:
        # 1. Tồn đầu kỳ: Tổng các giao dịch trước ngày 1 của tháng
        # (Logic: Tồn đầu = Tổng Nhập - Tổng Xuất từ thuở khai thiên lập địa đến trước ngày 1)
        begin_stock = InventoryLog.objects.filter(
            product=p, created_at__lt=start_date
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

        # 2. Nhập trong kỳ
        import_stock = InventoryLog.objects.filter(
            product=p, created_at__range=[start_date, end_date], change_type='IMPORT'
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

        # 3. Xuất trong kỳ (Lấy giá trị tuyệt đối vì lưu số âm)
        export_stock = InventoryLog.objects.filter(
            product=p, created_at__range=[start_date, end_date], change_type='EXPORT'
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
        export_stock = abs(export_stock) # Chuyển thành số dương để hiển thị

        # 4. Tồn cuối kỳ
        end_stock = begin_stock + import_stock - export_stock

        report_data.append({
            'name': p.name,
            'unit': p.unit,
            'begin': begin_stock,
            'import': import_stock,
            'export': export_stock,
            'end': end_stock
        })

    context = {
        'report_data': report_data,
        'month': month,
        'year': year,
        'months': range(1, 13),
        'years': range(today.year - 2, today.year + 3)
    }
    return render(request, 'inventory/inventory_report.html', context)