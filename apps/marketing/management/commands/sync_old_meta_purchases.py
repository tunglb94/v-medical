from django.core.management.base import BaseCommand
from apps.sales.models import Order
from apps.marketing.meta_capi import send_purchase_event_to_meta
import time
from datetime import datetime

class Command(BaseCommand):
    help = 'Đồng bộ doanh thu quá khứ của khách Facebook lên Meta CAPI'

    def handle(self, *args, **kwargs):
        # Lấy tất cả các đơn hàng ĐÃ THANH TOÁN của khách đến từ FACEBOOK
        paid_orders = Order.objects.filter(
            is_paid=True, 
            customer__source='FACEBOOK'
        ).select_related('customer')

        total = paid_orders.count()
        success = 0

        self.stdout.write(f"Tìm thấy {total} đơn hàng thoả mãn. Bắt đầu đồng bộ...")

        for order in paid_orders:
            # Chuyển đổi order_date (DateField) sang Datetime để lấy timestamp
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
            
            # Tạm dừng 0.2s để tránh bị Facebook block vì gửi request quá nhanh
            time.sleep(0.2)

        self.stdout.write(self.style.SUCCESS(f"Hoàn tất! Đã đồng bộ thành công {success}/{total} đơn hàng."))