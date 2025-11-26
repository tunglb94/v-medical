from django.urls import path
from . import views

urlpatterns = [
    path('', views.marketing_dashboard, name='marketing_dashboard'),
    path('delete/<int:pk>/', views.delete_report, name='delete_marketing_report'), # <--- MỚI
]