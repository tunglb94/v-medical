from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.sales.models import Order
from apps.marketing.meta_capi import send_purchase_event_to_meta

class Command(BaseCommand):
    help = 'Đẩy lại các đơn hàng cũ sang Meta CAPI để tính ROAS'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Số ngày quét ngược lại')

    def handle(self, *args, **options):
        days = options['days']
        start_date = timezone.now() - timedelta(days=days)
        
        # Lấy các đơn hàng đã thanh toán từ start_date
        # Lưu ý: Thay đổi 'PAID' thành status đúng trong database của bạn
        orders = Order.objects.filter(
            status='PAID', 
            created_at__gte=start_date
        )

        self.stdout.write(self.style.SUCCESS(f"Bắt đầu quét {orders.count()} đơn hàng trong {days} ngày qua..."))

        success_count = 0
        for order in orders:
            # Gọi hàm send_purchase_event_to_meta mới (đã có value và currency)
            result = send_purchase_event_to_meta(
                customer=order.customer,
                amount=order.total_amount,
                order_id=order.id,
                event_time=order.created_at
            )
            
            if result and 'error' not in result:
                success_count += 1
                self.stdout.write(f"--- Đã đẩy đơn #{order.id}: {order.total_amount} VND")
            else:
                self.stdout.write(self.style.ERROR(f"--- Lỗi đơn #{order.id}: {result}"))

        self.stdout.write(self.style.SUCCESS(f"=== HOÀN THÀNH: Đã đẩy thành công {success_count} đơn! ==="))