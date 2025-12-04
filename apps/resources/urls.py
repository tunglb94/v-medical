from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('<int:pk>/', views.document_detail, name='document_detail'),
    path('<int:pk>/test/', views.training_test, name='training_test'), # <-- Mới thêm
]