from django.core.management.base import BaseCommand
from apps.sales.models import Order
from apps.marketing.meta_capi import send_purchase_event_to_meta
import time
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Đồng bộ doanh thu quá khứ (7 ngày) của khách Facebook lên Meta CAPI'

    def handle(self, *args, **kwargs):
        # Tính toán mốc thời gian 7 ngày trước
        seven_days_ago = timezone.now().date() - timedelta(days=7)

        # Lấy tất cả các đơn hàng ĐÃ THANH TOÁN của khách đến từ FACEBOOK
        # VÀ CHỈ LẤY TRONG VÒNG 7 NGÀY QUA (để không bị lỗi Facebook từ chối)
        paid_orders = Order.objects.filter(
            is_paid=True, 
            customer__source='FACEBOOK',
            order_date__gte=seven_days_ago
        ).select_related('customer')

        total = paid_orders.count()
        success = 0

        self.stdout.write(f"Tìm thấy {total} đơn hàng hợp lệ (trong 7 ngày qua). Bắt đầu đồng bộ...")

        for order in paid_orders:
            dt = datetime.now()
            if order.order_date:
                dt = datetime.combine(order.order_date, datetime.min.time())

            response = send_purchase_event_to_meta(
                customer=order.customer,
                amount=order.total_amount,
                event_time=dt
            )
            
            if response and not response.get('error'):
                success += 1
                self.stdout.write(self.style.SUCCESS(f"Thành công: {order.customer.name} - {order.total_amount}đ"))
            else:
                self.stdout.write(self.style.ERROR(f"Lỗi {order.customer.name}: {response}"))
            
            time.sleep(0.2)

        self.stdout.write(self.style.SUCCESS(f"Hoàn tất! Đã đồng bộ thành công {success}/{total} đơn hàng."))