from django.urls import path
from . import views

app_name = 'service_calendar'

urlpatterns = [
    path('', views.technician_workspace, name='dashboard'),
    path('api/search-customer/', views.api_search_customer_services, name='api_search_customer'),
    path('create-session/', views.create_treatment_session, name='create_session'),

    # [THÊM MỚI] Sửa và Xóa session
    path('edit-session/', views.edit_treatment_session, name='edit_session'),
    path('delete-session/<int:session_id>/', views.delete_treatment_session, name='delete_session'),
]