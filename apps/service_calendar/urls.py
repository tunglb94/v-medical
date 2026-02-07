from django.urls import path
from . import views

app_name = 'service_calendar'

urlpatterns = [
    # Giao diện chính cho KTV
    path('', views.technician_workspace, name='dashboard'),
    
    # API tìm khách hàng và lấy dịch vụ đã mua
    path('api/search-customer/', views.api_search_customer_services, name='api_search_customer'),
    
    # Lưu buổi làm việc
    path('create-session/', views.create_treatment_session, name='create_session'),
]