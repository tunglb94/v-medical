from django.urls import path
from . import views

urlpatterns = [
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('payroll/', views.payroll_dashboard, name='payroll_dashboard'),
    path('contracts/', views.contract_management, name='contract_management'),
]