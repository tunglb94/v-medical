from django.urls import path
from . import views

urlpatterns = [
    path('attendance/toggle/', views.toggle_attendance, name='toggle_attendance'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('payroll/', views.payroll_dashboard, name='payroll_dashboard'),
]