from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from .models import Message
import json

User = get_user_model()

@login_required(login_url='/auth/login/')
def chat_home(request):
    # Lấy danh sách nhân viên trừ bản thân
    # Sắp xếp theo lần đăng nhập gần nhất để mô phỏng "Online"
    users = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by('-last_login')
    return render(request, 'chat/chat_home.html', {'users': users})

@login_required
def get_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Lấy tin nhắn 2 chiều
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | 
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    
    # Đánh dấu đã đọc cho các tin nhắn NGƯỜI KIA gửi cho MÌNH
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    data = []
    for msg in messages:
        data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'time': msg.timestamp.strftime('%H:%M %d/%m'),
            'is_me': msg.sender == request.user,
            'is_read': msg.is_read # Trả về trạng thái đã đọc
        })
    return JsonResponse(data, safe=False)

@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if content and receiver_id:
            receiver = get_object_or_404(User, id=receiver_id)
            msg = Message.objects.create(sender=request.user, receiver=receiver, content=content)
            return JsonResponse({'status': 'ok', 'time': msg.timestamp.strftime('%H:%M')})
            
    return JsonResponse({'status': 'error'}, status=400)