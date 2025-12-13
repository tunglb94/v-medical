from django.urls import path
from . import views

urlpatterns = [
    # Trang chủ Lễ tân (Dashboard)
    path('reception/', views.reception_dashboard, name='reception_home'),

    # API lấy dữ liệu lịch cho FullCalendar
    path('api/appointments/', views.get_appointments_api, name='get_appointments_api'),

    # Các hành động xử lý
    path('check-in/<int:appointment_id>/', views.checkin_appointment, name='checkin_appointment'),
    path('create/', views.create_appointment_reception, name='create_appointment_reception'),
    path('walk-in/', views.add_walkin_appointment, name='add_walkin_appointment'),
    path('finish/', views.finish_appointment, name='finish_appointment'),
]