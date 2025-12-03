from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Message
import json

User = get_user_model()

@login_required(login_url='/auth/login/')
def chat_home(request):
    # Lấy danh sách tất cả nhân viên trừ chính mình
    users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    return render(request, 'chat/chat_home.html', {'users': users})

@login_required
def get_messages(request, user_id):
    """API lấy tin nhắn giữa tôi và user_id"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Lấy tin nhắn 2 chiều (Tôi gửi & Họ gửi)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | 
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    
    # Đánh dấu đã đọc
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    data = []
    for msg in messages:
        data.append({
            'sender_id': msg.sender.id,
            'content': msg.content,
            'time': msg.timestamp.strftime('%H:%M %d/%m'),
            'is_me': msg.sender == request.user
        })
    return JsonResponse(data, safe=False)

@login_required
def send_message(request):
    """API gửi tin nhắn"""
    if request.method == 'POST':
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if content and receiver_id:
            receiver = get_object_or_404(User, id=receiver_id)
            Message.objects.create(sender=request.user, receiver=receiver, content=content)
            return JsonResponse({'status': 'ok'})
            
    return JsonResponse({'status': 'error'}, status=400)