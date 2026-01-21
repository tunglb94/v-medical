from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    
    # API Mới cho Room/Group
    path('api/create-direct/<int:user_id>/', views.create_direct_chat, name='create_direct_chat'),
    path('api/create-group/', views.create_group_chat, name='create_group_chat'),
    path('api/add-member/', views.add_member_to_group, name='add_member_to_group'),
    
    # API Chat (Đã sửa để dùng room_id)
    path('api/room/<int:room_id>/messages/', views.get_room_messages, name='get_room_messages'),
    path('api/send/', views.send_message, name='send_message'),
    
    # API Cũ (Giữ lại logic Announcement)
    path('create-announcement/', views.create_announcement, name='create_announcement'),
]