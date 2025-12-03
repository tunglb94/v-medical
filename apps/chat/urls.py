from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('api/get/<int:user_id>/', views.get_messages, name='get_messages'),
    path('api/send/', views.send_message, name='send_message'),
    path('api/unread/', views.count_unread, name='count_unread'),
    
    # MỚI THÊM
    path('create-announcement/', views.create_announcement, name='create_announcement'),
]