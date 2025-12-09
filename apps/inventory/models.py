from django.db import models
from django.conf import settings

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên thuốc/Vật tư")
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Mã SP (SKU)")
    unit = models.CharField(max_length=50, verbose_name="Đơn vị tính") # Hộp, Viên, Lọ...
    cost_price = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Giá vốn")
    stock = models.IntegerField(default=0, verbose_name="Tồn kho")
    min_stock = models.IntegerField(default=10, verbose_name="Cảnh báo tối thiểu")
    description = models.TextField(blank=True, verbose_name="Mô tả/Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.unit})"

    class Meta:
        verbose_name = "Sản phẩm/Thuốc"
        verbose_name_plural = "Kho hàng"

class InventoryLog(models.Model):
    TRANSACTION_TYPES = [
        ('IMPORT', 'Nhập kho'),
        ('EXPORT', 'Xuất kho/Sử dụng'),
        ('ADJUST', 'Kiểm kê/Điều chỉnh'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='logs')
    change_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="Loại GD")
    quantity = models.IntegerField(verbose_name="Số lượng thay đổi")
    stock_after = models.IntegerField(verbose_name="Tồn sau GD", null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người thực hiện")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']