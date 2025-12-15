from django.urls import path
from . import views

# Lưu ý: Không đặt app_name để tránh lỗi namespace phức tạp lúc này
urlpatterns = [
    # Dashboard Lễ tân
    path('reception/', views.reception_dashboard, name='reception_home'),

    # API lấy dữ liệu lịch (FullCalendar gọi cái này)
    path('api/appointments/', views.get_appointments_api, name='get_appointments_api'),

    # 3 URL quan trọng xử lý hành động (Template đang gọi tên này)
    path('check-in/<int:appointment_id>/', views.checkin_appointment, name='checkin_appointment'),
    path('finish/', views.finish_appointment, name='finish_appointment'),
    path('create/', views.create_appointment_reception, name='create_appointment_reception'),
    path('walk-in/', views.add_walkin_appointment, name='add_walkin_appointment'),
]