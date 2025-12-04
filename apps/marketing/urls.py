from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.marketing_dashboard, name='marketing_dashboard'),
    path('delete/<int:pk>/', views.delete_report, name='delete_marketing_report'),
    
    # Workspace (Lịch)
    path('workspace/', views.marketing_workspace, name='marketing_workspace'),
    path('api/tasks/', views.get_marketing_tasks_api, name='api_marketing_tasks'),

    # Content Ads
    path('content-ads/', views.content_ads_list, name='content_ads_list'),
    path('content-ads/edit/<int:pk>/', views.content_ads_edit, name='content_ads_edit'),
    path('content-ads/delete/<int:pk>/', views.content_ads_delete, name='content_ads_delete'),
    
    # API Feedback
    path('api/task-feedback/<int:task_id>/', views.get_task_feedback_api, name='api_task_feedback'),
]