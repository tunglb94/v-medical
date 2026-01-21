from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import views từ Authentication
from apps.authentication.views import root_view, global_search 

# Import views từ Telesales
from apps.telesales.views import telesale_dashboard 

# Import views từ Bookings
# [CẬP NHẬT] Thêm 'delete_appointment_reception' và 'noshow_appointment'
from apps.bookings.views import (
    reception_dashboard, checkin_appointment, create_appointment_reception,
    finish_appointment, add_walkin_appointment, get_appointments_api,
    edit_appointment, delete_appointment_reception, noshow_appointment
)

# Import views từ Sales
from apps.sales.views import (
    revenue_dashboard, print_invoice, admin_dashboard, debt_manager,
    update_order_details
)

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

    # --- 4. TELESALE ---
    path('telesale/', include('apps.telesales.urls')),
    
    # --- 5. RECEPTION (LỄ TÂN) ---
    path('reception/', reception_dashboard, name='reception_home'),
    path('reception/checkin/<int:appointment_id>/', checkin_appointment, name='checkin_appointment'),
    path('reception/edit/<int:appointment_id>/', edit_appointment, name='edit_appointment'),
    path('reception/create-appointment/', create_appointment_reception, name='create_appointment_reception'),
    path('reception/finish/', finish_appointment, name='finish_appointment'),
    path('reception/walk-in/', add_walkin_appointment, name='add_walkin_appointment'),
    path('api/calendar/appointments/', get_appointments_api, name='get_appointments_api'),

    # [MỚI] URL Xóa Lịch và Báo Khách Không Đến
    path('reception/delete/<int:appointment_id>/', delete_appointment_reception, name='delete_appointment_reception'),
    path('reception/noshow/<int:appointment_id>/', noshow_appointment, name='noshow_appointment'),

    # --- 6. SALES & BÁO CÁO ---
    path('sales/report/', revenue_dashboard, name='sales_report'),
    path('sales/invoice/<int:order_id>/', print_invoice, name='print_invoice'),
    path('sales/update-details/', update_order_details, name='update_order_details'),
    path('sales/debt/', debt_manager, name='debt_manager'),

    # --- 7. MODULES KHÁC ---
    path('customers/', include('apps.customers.urls')), 
    path('marketing/', include('apps.marketing.urls')), 
    path('hr/', include('apps.hr.urls')),
    path('chat/', include('apps.chat.urls')), 
    path('resources/', include('apps.resources.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('service-calendar/', include('apps.service_calendar.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])