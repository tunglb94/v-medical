from django.contrib import admin
from django.urls import path, include # Nhớ import include
from django.conf import settings
from django.conf.urls.static import static

# Import views từ Telesales
from apps.telesales.views import telesale_dashboard, add_customer_manual

# Import views từ Bookings (Lễ tân)
from apps.bookings.views import (
    reception_dashboard, 
    checkin_appointment, 
    create_appointment_reception,
    finish_appointment,
    add_walkin_appointment
)

# Import views từ Sales (Báo cáo, Hóa đơn, Admin Dashboard)
from apps.sales.views import (
    revenue_dashboard, 
    print_invoice, 
    admin_dashboard # <-- View tổng quan cho Sếp
)

urlpatterns = [
    # --- 1. ADMIN DJANGO ---
    path('admin/', admin.site.urls),
    
    # --- 2. AUTHENTICATION (ĐĂNG NHẬP/XUẤT) ---
    path('auth/', include('apps.authentication.urls')), 

    # --- 3. DASHBOARD TỔNG QUAN (DÀNH CHO SẾP/ADMIN) ---
    path('dashboard/', admin_dashboard, name='admin_dashboard'),

    # --- 4. TELESALE (TRANG CHỦ) ---
    path('', telesale_dashboard, name='home'),
    path('add-customer/', add_customer_manual, name='add_customer'),
    
    # --- 5. RECEPTION (LỄ TÂN) ---
    path('reception/', reception_dashboard, name='reception_home'),
    path('reception/checkin/<int:appointment_id>/', checkin_appointment, name='checkin'),
    path('reception/create-appointment/', create_appointment_reception, name='reception_create_appointment'),
    path('reception/finish/', finish_appointment, name='reception_finish'),
    path('reception/walk-in/', add_walkin_appointment, name='reception_walkin'),

    # --- 6. SALES & BÁO CÁO ---
    path('sales/report/', revenue_dashboard, name='sales_report'),
    path('sales/invoice/<int:order_id>/', print_invoice, name='print_invoice'),

    # --- 7. CUSTOMER MANAGEMENT (QUẢN LÝ KHÁCH HÀNG) ---
    path('customers/', include('apps.customers.urls')), 
    
    # ...
    path('marketing/', include('apps.marketing.urls')), # <--- THÊM DÒNG NÀY
]

# Cấu hình hiển thị file tĩnh (CSS, Ảnh) khi Debug = True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])