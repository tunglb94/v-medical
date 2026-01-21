from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Message, Announcement, Room
import json

User = get_user_model()

@login_required(login_url='/auth/login/')
def chat_home(request):
    # Lấy danh sách Users để tạo chat mới
    users = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by('first_name')
    
    # Lấy danh sách các phòng chat mà user đang tham gia
    my_rooms = request.user.chat_rooms.all().order_by('-updated_at')
    
    # Xử lý tên phòng hiển thị (Nếu là Direct thì hiện tên người kia, nếu Group thì hiện tên nhóm)
    room_data = []
    for room in my_rooms:
        display_name = room.name
        avatar_char = "G"
        is_group = (room.type == 'GROUP')
        
        if not is_group:
            # Tìm người kia trong phòng 2 người
            other_member = room.members.exclude(id=request.user.id).first()
            if other_member:
                display_name = f"{other_member.last_name} {other_member.first_name}"
                avatar_char = other_member.username[0].upper()
            else:
                display_name = "Chat một mình"
        else:
            avatar_char = room.name[0].upper() if room.name else "G"

        room_data.append({
            'id': room.id,
            'name': display_name,
            'avatar': avatar_char,
            'is_group': is_group,
            'last_msg': room.messages.last().content if room.messages.exists() else "Trò chuyện mới",
            'updated_at': room.updated_at
        })

    # --- GIỮ NGUYÊN: LẤY THÔNG BÁO ---
    announcements = Announcement.objects.filter(is_active=True).filter(
        Q(target_role='ALL') | Q(target_role=request.user.role)
    )

    return render(request, 'chat/chat_home.html', {
        'users': users, 
        'rooms': room_data,
        'announcements': announcements,
        'current_user_id': request.user.id
    })

# --- API TẠO PHÒNG CHAT 1-1 (DIRECT) ---
@login_required
def create_direct_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    # Kiểm tra xem đã có phòng 1-1 giữa 2 người chưa
    # Logic: Phòng loại DIRECT có member là user hiện tại VÀ target_user
    existing_rooms = Room.objects.filter(type='DIRECT', members=request.user).filter(members=target_user)
    
    if existing_rooms.exists():
        room = existing_rooms.first()
    else:
        room = Room.objects.create(type='DIRECT')
        room.members.add(request.user, target_user)
        # 1-1 thì không cần admin
    
    return JsonResponse({'status': 'ok', 'room_id': room.id, 'room_name': f"{target_user.last_name} {target_user.first_name}"})

# --- API TẠO NHÓM (GROUP) ---
@login_required
def create_group_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        group_name = data.get('group_name')
        member_ids = data.get('members', []) # Danh sách ID user
        
        if group_name and member_ids:
            room = Room.objects.create(name=group_name, type='GROUP')
            room.members.add(request.user) # Thêm mình
            room.admins.add(request.user)  # Set mình làm trưởng nhóm
            
            for uid in member_ids:
                try:
                    u = User.objects.get(id=uid)
                    room.members.add(u)
                except User.DoesNotExist:
                    pass
            
            return JsonResponse({'status': 'ok', 'room_id': room.id})
            
    return JsonResponse({'status': 'error'}, status=400)

# --- API THÊM THÀNH VIÊN VÀO NHÓM ---
@login_required
def add_member_to_group(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        
        try:
            room = Room.objects.get(id=room_id, type='GROUP')
            # Kiểm tra quyền: Chỉ Admin nhóm hoặc thành viên (tuỳ logic, ở đây cho Admin)
            if request.user in room.admins.all():
                user_to_add = User.objects.get(id=user_id)
                room.members.add(user_to_add)
                return JsonResponse({'status': 'ok', 'message': f'Đã thêm {user_to_add.username}'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Bạn không phải trưởng nhóm'}, status=403)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

# --- API LẤY TIN NHẮN (THEO ROOM) ---
@login_required
def get_room_messages(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Bảo mật: Chỉ thành viên mới xem được
    if request.user not in room.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    messages = room.messages.select_related('sender', 'parent').order_by('timestamp')
    
    data = []
    for msg in messages:
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
            'sender_name': f"{msg.sender.last_name} {msg.sender.first_name}",
            'avatar': msg.sender.username[0].upper(),
            'content': msg.content,
            'time': msg.timestamp.strftime('%H:%M %d/%m'),
            'is_me': msg.sender == request.user,
            'parent': parent_data
        })
    return JsonResponse(data, safe=False)

# --- API GỬI TIN NHẮN (VÀO ROOM) ---
@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_id = data.get('room_id') # Gửi vào Room chứ k phải receiver_id
        content = data.get('content')
        parent_id = data.get('parent_id')
        
        if content and room_id:
            room = get_object_or_404(Room, id=room_id)
            if request.user not in room.members.all():
                return JsonResponse({'status': 'error', 'message': 'Not in room'}, status=403)

            parent_msg = None
            if parent_id:
                try:
                    parent_msg = Message.objects.get(id=parent_id)
                except Message.DoesNotExist:
                    pass

            Message.objects.create(room=room, sender=request.user, content=content, parent=parent_msg)
            
            # Cập nhật thời gian phòng để nhảy lên đầu
            room.save() 
            
            return JsonResponse({'status': 'ok'})
            
    return JsonResponse({'status': 'error'}, status=400)

# --- GIỮ NGUYÊN: TẠO THÔNG BÁO ---
@login_required
def create_announcement(request):
    if request.method == 'POST' and (request.user.role == 'ADMIN' or request.user.is_superuser):
        title = request.POST.get('title')
        content = request.POST.get('content')
        target = request.POST.get('target', 'ALL')
        
        if title and content:
            Announcement.objects.create(
                creator=request.user, title=title, content=content, target_role=target
            )
            return redirect('chat_home')
    return redirect('chat_home')