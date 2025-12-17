from django.urls import path
from . import views

app_name = 'service_calendar' # Namespace để không trùng với app bookings

urlpatterns = [
    path('', views.calendar_dashboard, name='dashboard'),
    path('add/', views.quick_add_appointment, name='quick_add'),
    path('remind/<int:appt_id>/', views.confirm_reminder, name='confirm_reminder'),
]