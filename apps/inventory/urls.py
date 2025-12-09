from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('transaction/<int:product_id>/', views.inventory_transaction, name='inventory_transaction'),
    path('edit/<int:pk>/', views.edit_product, name='edit_product'), # <--- THÊM DÒNG NÀY
    path('report/', views.inventory_report, name='inventory_report'),
]