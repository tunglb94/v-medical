from django.urls import path
from . import views

urlpatterns = [
    # Dashboard cũ
    path('', views.marketing_dashboard, name='marketing_dashboard'),
    path('delete/<int:pk>/', views.delete_report, name='delete_marketing_report'),
    
    # Workspace mới
    path('workspace/', views.marketing_workspace, name='marketing_workspace'),
    path('api/tasks/', views.get_marketing_tasks_api, name='api_marketing_tasks'),
]