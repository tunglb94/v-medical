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
    users = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by('-last_login')
    return render(request, 'chat/chat_home.html', {'users': users})

@login_required
def get_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | 
        Q(sender=other_user, receiver=request.user)
    ).select_related('parent').order_by('timestamp') # Thêm select_related để tối ưu
    
    # Đánh dấu đã đọc
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    data = []
    for msg in messages:
        # Xử lý thông tin tin nhắn gốc nếu là Reply
        parent_data = None
        if msg.parent:
            parent_data = {
                'id': msg.parent.id,
                'content': msg.parent.content[:50] + "..." if len(msg.parent.content) > 50 else msg.parent.content,
                'sender': msg.parent.sender.last_name or msg.parent.sender.username
            }

        data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'time': msg.timestamp.strftime('%H:%M %d/%m'),
            'is_me': msg.sender == request.user,
            'is_read': msg.is_read,
            'parent': parent_data # Gửi kèm info tin nhắn gốc
        })
    return JsonResponse(data, safe=False)

@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        parent_id = data.get('parent_id') # Lấy ID tin nhắn đang trả lời (nếu có)
        
        if content and receiver_id:
            receiver = get_object_or_404(User, id=receiver_id)
            
            parent_msg = None
            if parent_id:
                try:
                    parent_msg = Message.objects.get(id=parent_id)
                except Message.DoesNotExist:
                    pass

            Message.objects.create(
                sender=request.user, 
                receiver=receiver, 
                content=content,
                parent=parent_msg
            )
            return JsonResponse({'status': 'ok'})
            
    return JsonResponse({'status': 'error'}, status=400)

# --- API ĐẾM TIN NHẮN CHƯA ĐỌC (CHO CHUÔNG THÔNG BÁO) ---
@login_required
def count_unread(request):
    count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({'count': count})