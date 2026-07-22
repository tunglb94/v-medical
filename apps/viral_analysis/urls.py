from django.urls import path

from . import views

app_name = 'viral_analysis'

urlpatterns = [
    path('', views.submission_list, name='submission_list'),
    path('new/', views.submission_create, name='submission_create'),
    path('<int:submission_id>/', views.submission_detail, name='submission_detail'),
]
