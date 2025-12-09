from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce, Abs
from django.utils import timezone
from datetime import datetime
import pandas as pd 

from apps.authentication.decorators import allowed_users
from .models import Product, InventoryLog

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_list(request):
    # --- 1. TÍNH TOÁN SỐ LIỆU ---
    today = timezone.now()
    start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    products = Product.objects.annotate(
        import_period=Coalesce(
            Sum('logs__quantity', filter=Q(logs__change_type='IMPORT', logs__created_at__gte=start_month)), 
            0
        ),
        export_period=Abs(Coalesce(
            Sum('logs__quantity', filter=Q(logs__change_type='EXPORT', logs__created_at__gte=start_month)), 
            0
        ))
    ).annotate(
        beginning_stock=F('stock') - F('import_period') + F('export_period')
    ).order_by('name')
    
    # --- 2. LỌC & TÌM KIẾM ---
    q = request.GET.get('q')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(code__icontains=q))

    status_filter = request.GET.get('status')
    if status_filter == 'out_of_stock':
        products = products.filter(stock=0)
    elif status_filter == 'low_stock':
        products = products.filter(stock__lte=F('min_stock'), stock__gt=0)
    elif status_filter == 'in_stock':
        products = products.filter(stock__gt=F('min_stock'))

    total_count = Product.objects.count()
    low_stock_count = Product.objects.filter(stock__lte=F('min_stock')).count()

    # --- 3. XỬ LÝ THÊM MỚI (POST) ---
    if request.method == 'POST':
        if 'add_product' in request.POST:
            name = request.POST.get('name')
            unit = request.POST.get('unit') or 'Hộp' 
            min_stock = request.POST.get('min_stock') or 10
            initial_stock = int(request.POST.get('stock') or 0)
            
            try:
                prod = Product.objects.create(
                    name=name, unit=unit, min_stock=min_stock, stock=initial_stock
                )
                if initial_stock > 0:
                    InventoryLog.objects.create(
                        product=prod, change_type='ADJUST', quantity=initial_stock,
                        stock_after=initial_stock, user=request.user, note="Tồn đầu kỳ (Khởi tạo)"
                    )
                messages.success(request, f"Đã thêm: {name}")
            except Exception as e:
                messages.error(request, f"Lỗi: {str(e)}")
            return redirect('inventory_list')
            
        if 'import_file' in request.FILES:
            excel_file = request.FILES['import_file']
            try:
                df = pd.read_excel(excel_file)
                count = 0
                for index, row in df.iterrows():
                    name = str(row.get('Ten', '')).strip()
                    if name:
                        unit = str(row.get('DonVi', 'Hộp')).strip()
                        stock = int(row.get('TonDau', 0))
                        obj, created = Product.objects.get_or_create(
                            name=name,
                            defaults={'unit': unit, 'stock': stock}
                        )
                        if created and stock > 0:
                             InventoryLog.objects.create(
                                product=obj, change_type='ADJUST', quantity=stock,
                                stock_after=stock, user=request.user, note="Import Excel"
                            )
                        count += 1
                messages.success(request, f"Đã nhập {count} sản phẩm!")
            except Exception as e:
                messages.error(request, f"Lỗi file: {str(e)}")
            return redirect('inventory_list')

    context = {
        'products': products,
        'low_stock_count': low_stock_count,
        'total_count': total_count,
        'current_filter': status_filter,
        'search_query': q,
        'current_month': today.month
    }
    return render(request, 'inventory/inventory_list.html', context)

# --- 4. HÀM SỬA SẢN PHẨM (MỚI THÊM) ---
@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        old_stock = product.stock
        
        # Cập nhật thông tin cơ bản
        product.name = request.POST.get('name')
        product.unit = request.POST.get('unit')
        product.min_stock = int(request.POST.get('min_stock', 0))
        
        # Xử lý sửa tồn kho (Nếu có thay đổi số lượng)
        new_stock_str = request.POST.get('stock')
        if new_stock_str:
            new_stock = int(new_stock_str)
            if new_stock != old_stock:
                diff = new_stock - old_stock
                product.stock = new_stock
                
                # Ghi log điều chỉnh (Để báo cáo vẫn đúng)
                InventoryLog.objects.create(
                    product=product,
                    change_type='ADJUST',
                    quantity=diff,
                    stock_after=new_stock,
                    user=request.user,
                    note=f"Sửa sai sót: {old_stock} -> {new_stock}"
                )
        
        product.save()
        messages.success(request, f"Đã cập nhật thông tin: {product.name}")
        return redirect('inventory_list')
        
    return redirect('inventory_list') 

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
        else: 
            product.stock += qty
            final_qty = qty

        product.save()

        InventoryLog.objects.create(
            product=product, change_type=trans_type, quantity=final_qty,
            stock_after=product.stock, user=request.user, note=note
        )
        messages.success(request, "Giao dịch thành công!")
        
    return redirect('inventory_list')

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_report(request):
    today = timezone.now()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    products = Product.objects.all().order_by('name')
    report_data = []

    for p in products:
        begin_stock = InventoryLog.objects.filter(
            product=p, created_at__lt=start_date
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

        import_stock = InventoryLog.objects.filter(
            product=p, created_at__range=[start_date, end_date], change_type='IMPORT'
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

        export_stock = InventoryLog.objects.filter(
            product=p, created_at__range=[start_date, end_date], change_type='EXPORT'
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
        export_stock = abs(export_stock)

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