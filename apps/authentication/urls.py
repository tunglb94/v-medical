from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile & Đổi mật khẩu
    path('profile/', views.user_profile, name='user_profile'), # <--- MỚI
    
    # Quản lý nhân sự (Giữ nguyên)
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_create_update, name='staff_create'),
    path('staff/edit/<int:pk>/', views.staff_create_update, name='staff_edit'),
    path('staff/delete/<int:pk>/', views.staff_delete, name='staff_delete'),
]