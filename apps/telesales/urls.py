from django.urls import path
from . import views

urlpatterns = [
    # Telesale Dashboard (Thường là telesale_home)
    path('', views.telesale_dashboard, name='telesale_home'),
    
    # BỔ SUNG: Đường dẫn cho chức năng thêm khách hàng thủ công
    path('add-manual/', views.add_customer_manual, name='add_customer_manual'),
    
    # BỔ SUNG: Đường dẫn cho trang báo cáo telesale
    path('report/', views.telesale_report, name='telesale_report'), 
]