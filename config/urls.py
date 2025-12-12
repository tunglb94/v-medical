from django.contrib import admin
from django.urls import path, include

from apps.authentication.views import root_view, admin_dashboard, global_search
from apps.bookings.views import (
    reception_dashboard, 
    checkin_appointment, 
    create_appointment_reception, 
    finish_appointment, 
    add_walkin_appointment, 
    get_appointments_api
)
from apps.sales.views import revenue_dashboard, print_invoice

urlpatterns = [
    # --- 0. TRANG CHỦ ĐIỀU HƯỚNG ---
    path('', root_view, name='root'), 
    path('search/', global_search, name='global_search'), 

    # --- 1. ADMIN DJANGO ---
    path('admin/', admin.site.urls),
    
    # --- 2. AUTHENTICATION ---
    path('auth/', include('apps.authentication.urls')), 

    # --- 3. DASHBOARD ---
    path('dashboard/', admin_dashboard, name='admin_dashboard'),

    # --- 4. TELESALE (Sử dụng include để gom tất cả URL Telesale) ---
    path('telesale/', include('apps.telesales.urls')), 

    # --- 5. RECEPTION (LỄ TÂN) ---
    path('reception/', reception_dashboard, name='reception_home'),
    path('reception/checkin/<int:appointment_id>/', checkin_appointment, name='checkin'),
    path('reception/create-appointment/', create_appointment_reception, name='reception_create_appointment'),
    # ĐÃ SỬA: Đổi tên thành 'finish_appointment' để khớp với template HTML
    path('reception/finish/', finish_appointment, name='finish_appointment'), 
    path('reception/walk-in/', add_walkin_appointment, name='reception_walkin'),
    
    # API cho Lịch
    path('api/calendar/appointments/', get_appointments_api, name='api_appointments'),

    # --- 6. SALES & BÁO CÁO ---
    path('sales/report/', revenue_dashboard, name='sales_report'),
    path('sales/invoice/<int:order_id>/', print_invoice, name='print_invoice'),

    # --- 7. MODULES KHÁC ---
    path('customers/', include('apps.customers.urls')), 
    path('marketing/', include('apps.marketing.urls')), 
    path('hr/', include('apps.hr.urls')),
    
    # --- 8. CHAT ---
    path('chat/', include('apps.chat.urls')), 

    path('resources/', include('apps.resources.urls')),
    path('inventory/', include('apps.inventory.urls')),
]