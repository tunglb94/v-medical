# apps/sales/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Báo cáo doanh thu
    path('report/', views.revenue_dashboard, name='sales_report'), 
    
    # [MỚI] Trang cấu hình hoa hồng
    # Tên (name) ở đây chính là cái được gọi trong {% url '...' %}
    path('commission-config/', views.service_commission_config, name='service_commission_config'),
    
    # Các URL khác
    path('debt/', views.debt_manager, name='debt_manager'),
    path('update-order/', views.update_order_details, name='update_order_details'),
    path('invoice/<int:order_id>/', views.print_invoice, name='print_invoice'),
]