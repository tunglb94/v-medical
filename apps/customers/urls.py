from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
]