from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.authentication.decorators import allowed_users
from .models import Product, InventoryLog

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_list(request):
    products = Product.objects.all().order_by('name')
    
    # Tìm kiếm
    q = request.GET.get('q')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(code__icontains=q))

    # Cảnh báo sắp hết hàng
    low_stock_products = products.filter(stock__lte=models.F('min_stock'))

    if request.method == 'POST':
        # Xử lý form thêm mới nhanh
        if 'add_product' in request.POST:
            name = request.POST.get('name')
            unit = request.POST.get('unit')
            min_stock = request.POST.get('min_stock')
            try:
                Product.objects.create(name=name, unit=unit, min_stock=min_stock)
                messages.success(request, "Đã thêm sản phẩm mới!")
            except Exception as e:
                messages.error(request, f"Lỗi: {str(e)}")
            return redirect('inventory_list')

    context = {
        'products': products,
        'low_stock_count': low_stock_products.count()
    }
    return render(request, 'inventory/inventory_list.html', context)

@login_required(login_url='/auth/login/')
@allowed_users(allowed_roles=['ADMIN', 'RECEPTIONIST'])
def inventory_transaction(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        trans_type = request.POST.get('type') # IMPORT / EXPORT
        qty = int(request.POST.get('quantity', 0))
        note = request.POST.get('note', '')

        if qty <= 0:
            messages.error(request, "Số lượng phải lớn hơn 0")
            return redirect('inventory_list')

        # Tính toán tồn kho mới
        if trans_type == 'EXPORT':
            if product.stock < qty:
                messages.error(request, f"Kho không đủ! Hiện còn {product.stock} {product.unit}")
                return redirect('inventory_list')
            product.stock -= qty
            final_qty = -qty # Lưu số âm vào log để dễ cộng trừ
        else: # IMPORT
            product.stock += qty
            final_qty = qty

        product.save()

        # Lưu lịch sử
        InventoryLog.objects.create(
            product=product,
            change_type=trans_type,
            quantity=final_qty,
            stock_after=product.stock,
            user=request.user,
            note=note
        )
        
        action = "Nhập" if trans_type == 'IMPORT' else "Xuất"
        messages.success(request, f"Đã {action} {qty} {product.unit} - {product.name}")
        
    return redirect('inventory_list')