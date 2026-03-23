from django.urls import path
from . import views

urlpatterns = [
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('payroll/', views.payroll_dashboard, name='payroll_dashboard'),
    path('contracts/', views.contract_management, name='contract_management'),
    
    # Tính năng nghỉ phép
    path('leaves/', views.leave_request_list, name='leave_list'),
    path('leaves/create/', views.leave_request_create, name='leave_create'),
    path('leaves/update/<int:leave_id>/', views.leave_request_update, name='leave_update'),
]