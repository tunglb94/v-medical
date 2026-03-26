from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order
from apps.bookings.models import Appointment 

# [MỚI] Import hàm gửi dữ liệu Meta CAPI
from apps.marketing.meta_capi import send_purchase_event_to_meta 

# --- [MỚI] TỰ ĐỘNG TẠO ĐƠN TỪ LỊCH HẸN VỚI ĐÚNG NGÀY ---
@receiver(post_save, sender=Appointment)
def create_order_from_appointment(sender, instance, created, **kwargs):
    """
    Khi Lịch hẹn chuyển sang trạng thái ARRIVED hoặc COMPLETED,
    tự động tạo đơn hàng tương ứng và lấy NGÀY CỦA LỊCH HẸN (Backdate).
    """
    if instance.status in ['ARRIVED', 'COMPLETED']:
        # Lấy dịch vụ (Cần đảm bảo Appointment có trường service)
        service = getattr(instance, 'service', None)
        
        if service:
            # get_or_create để tránh tạo trùng
            order, created = Order.objects.get_or_create(
                appointment=instance,
                defaults={
                    'customer': instance.customer,
                    'service': service,
                    'assigned_consultant': getattr(instance, 'assigned_consultant', None),
                    
                    # [FIX LỖI] Lấy ngày của lịch hẹn gán cho ngày đơn hàng
                    # Thay vì để mặc định là ngày hôm nay (date.today)
                    'order_date': instance.appointment_date, 
                    
                    'note': f"Đơn hàng tạo tự động từ lịch hẹn {instance.id}"
                }
            )
            
            # Nếu đơn hàng đã tồn tại (do tạo trước đó bị sai ngày),
            # ta cập nhật lại ngày cho khớp với lịch hẹn
            if not created and order.order_date != instance.appointment_date:
                order.order_date = instance.appointment_date
                order.save(update_fields=['order_date'])

# --- CẬP NHẬT RANKING KHÁCH HÀNG ---
@receiver(post_save, sender=Order)
def update_customer_ranking_on_save(sender, instance, created, **kwargs):
    if instance.customer:
        instance.customer.update_ranking()

@receiver(post_delete, sender=Order)
def update_customer_ranking_on_delete(sender, instance, **kwargs):
    if instance.customer:
        instance.customer.update_ranking()

# --- [MỚI] GỬI SỰ KIỆN PURCHASE LÊN META CAPI ---
@receiver(post_save, sender=Order)
def trigger_meta_capi_on_payment(sender, instance, created, **kwargs):
    """
    Tự động báo cáo doanh thu lên Facebook khi đơn hàng được thanh toán đủ.
    """
    if instance.is_paid:
        customer = instance.customer
        
        # Chỉ gửi thông tin về Meta nếu khách có nguồn từ FACEBOOK
        if customer and customer.source == 'FACEBOOK':
            try:
                # Gửi sự kiện Purchase với tổng doanh thu (total_amount)
                response = send_purchase_event_to_meta(
                    customer=customer, 
                    amount=instance.total_amount
                )
                print(f"Đã gửi Meta CAPI - Khách: {customer.name} | Phản hồi: {response}")
            except Exception as e:
                print(f"Lỗi khi gửi Meta CAPI tại signal: {e}")