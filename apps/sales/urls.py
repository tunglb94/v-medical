from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.revenue_dashboard, name='sales_report'),
    path('debt/', views.debt_manager, name='debt_manager'),
    path('update-order/', views.update_order_details, name='update_order_details'),
    path('invoice/<int:order_id>/', views.print_invoice, name='print_invoice'),
    
    # [MỚI] Trang cấu hình hoa hồng (Chỉ Admin)
    path('commission-config/', views.service_commission_config, name='service_commission_config'),
    
    # Dashboard Admin (Nếu cần tách URL riêng, còn không nó đã được include ở config)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]