from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('transaction/<int:product_id>/', views.inventory_transaction, name='inventory_transaction'),
    path('report/', views.inventory_report, name='inventory_report'), # <--- Thêm dòng này
]