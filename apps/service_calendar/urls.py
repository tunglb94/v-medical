from django.urls import path
from . import views

app_name = 'service_calendar'

urlpatterns = [
    path('', views.calendar_dashboard, name='dashboard'),
    path('add/', views.quick_add_appointment, name='quick_add'),
    path('remind/<int:appt_id>/', views.confirm_reminder, name='confirm_reminder'),
    
    # [MỚI] URL cập nhật trạng thái
    path('update-status/', views.update_appointment_status, name='update_status'),
]