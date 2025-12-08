from django.urls import path
from . import views

urlpatterns = [
    # BỔ SUNG: Thay thế đường dẫn gốc bằng Dashboard view
    path('', views.telesale_dashboard, name='telesale_home'),
    
    # HOÀN THIỆN: Đường dẫn cho chức năng thêm khách hàng thủ công
    path('add-manual/', views.add_customer_manual, name='add_customer_manual'),
    # BỔ SUNG: Đặt tên cho đường dẫn add-customer cũ (nếu có sử dụng ở đâu đó)
    path('add-customer/', views.add_customer_manual, name='add_customer'),
    
    # HOÀN THIỆN: Đường dẫn cho trang báo cáo telesale
    path('report/', views.telesale_report, name='telesale_report'), 
]