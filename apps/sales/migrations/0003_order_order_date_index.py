from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Chỉ thêm index cho order_date để tối ưu tốc độ lọc báo cáo doanh thu.
    Viết tay (không dùng makemigrations) vì models.py hiện có nhiều field
    (original_price, payment_method, total_sessions, Service.base_price,
    Service.commission_rate, ...) chưa từng được migrate kể từ migration 0002 -
    chạy autodetector sẽ gộp toàn bộ phần lệch đó vào, rất rủi ro cho production.
    """

    dependencies = [
        ('sales', '0002_service_alter_order_total_amount_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_date'], name='sales_order_order_date_idx'),
        ),
    ]
