# v-medical copy/apps/bookings/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Lễ Tân (sử dụng name='reception_home' trong template)
    path('reception/', views.reception_dashboard, name='reception_home'),
    
    # API lấy dữ liệu cho FullCalendar
    path('api/appointments/', views.get_appointments_api, name='get_appointments_api'),

    # 4. TẠO LỊCH NHANH (KHÁCH CŨ)
    path('appointment/create/', views.create_appointment_reception, name='create_appointment_reception'),
    
    # 5. KHÁCH VÃNG LAI (FIX LỖI NÀY)
    path('walkin/add/', views.add_walkin_appointment, name='add_walkin_appointment'),
    
    # 3. CHECK-IN (Cần appointment_id)
    path('checkin/<int:appointment_id>/', views.checkin_appointment, name='checkin'),
    
    # 6. CHỐT CA
    path('appointment/finish/', views.finish_appointment, name='finish_appointment'),
]