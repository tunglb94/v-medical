from django.urls import path

from . import views

app_name = 'viral_analysis'

urlpatterns = [
    path('', views.submission_list, name='submission_list'),
    path('new/', views.submission_create, name='submission_create'),
    path('ideas/', views.idea_suggest, name='idea_suggest'),
    path('<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('<int:submission_id>/delete/', views.submission_delete, name='submission_delete'),
]
