from django.urls import path
from . import views

urlpatterns = [
    path('', views.telesale_dashboard, name='telesale_home'),
    path('add-customer/', views.add_customer_manual, name='add_customer'),
    path('report/', views.telesale_report, name='telesale_report'), # <--- MỚI
]