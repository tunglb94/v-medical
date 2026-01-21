from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from .models import Message, Announcement, Room
import json
import uuid
import io
import os

# Thư viện xử lý ảnh (Cần cài đặt: pip install Pillow)
try:
    from PIL import Image
except ImportError:
    import sys
    # Fallback nếu chưa cài Pillow (để tránh lỗi crash server ngay lập tức)
    print("WARNING: Pillow not installed. Image upload will fail.", file=sys.stderr)

User = get_user_model()

# --- HÀM HỖ TRỢ NÉN & BẢO MẬT ẢNH ---
def process_image(uploaded_file):
    try:
        # 1. Kiểm tra định dạng (Chống đổi đuôi file exe/php thành jpg)
        img = Image.open(uploaded_file)
        
        # Chỉ chấp nhận các định dạng an toàn
        if img.format not in ['JPEG', 'PNG', 'WEBP']:
            return None, "Định dạng file không hỗ trợ (Chỉ nhận JPG, PNG, WEBP)"

        # 2. Xóa Metadata (Nơi hacker hay giấu mã độc)
        if hasattr(img, 'getdata'):
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)
            img = image_without_exif

        # 3. Resize ảnh (Tiết kiệm dung lượng)
        max_width = 1024
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int((float(img.height) * float(ratio)))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # 4. Chuyển đổi sang RGB (để lưu thống nhất thành JPEG)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 5. Nén ảnh
        output_io = io.BytesIO()
        # Quality=60: Giảm dung lượng cực mạnh nhưng vẫn nhìn rõ
        img.save(output_io, format='JPEG', quality=60, optimize=True) 
        
        # 6. Đổi tên file ngẫu nhiên
        filename = f"{uuid.uuid4()}.jpg"
        
        # Trả về file đã xử lý
        return ContentFile(output_io.getvalue(), name=filename), None

    except Exception as e:
        return None, str(e)

@login_required(login_url='/auth/login/')
def chat_home(request):
    users = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by('first_name')
    my_rooms = request.user.chat_rooms.all().order_by('-updated_at')
    
    room_data = []
    for room in my_rooms:
        display_name = room.name
        avatar_char = "G"
        is_group = (room.type == 'GROUP')
        
        if not is_group:
            other_member = room.members.exclude(id=request.user.id).first()
            if other_member:
                display_name = f"{other_member.last_name} {other_member.first_name}"
                avatar_char = other_member.username[0].upper()
            else:
                display_name = "Chat một mình"
        else:
            avatar_char = room.name[0].upper() if room.name else "G"

        last_msg_content = "Trò chuyện mới"
        last_msg = room.messages.last()
        if last_msg:
            if last_msg.attachment:
                last_msg_content = "📎 Đã gửi một ảnh"
            else:
                last_msg_content = last_msg.content

        room_data.append({
            'id': room.id,
            'name': display_name,
            'avatar': avatar_char,
            'is_group': is_group,
            'last_msg': last_msg_content,
            'updated_at': room.updated_at
        })

    announcements = Announcement.objects.filter(is_active=True).filter(
        Q(target_role='ALL') | Q(target_role=request.user.role)
    )

    return render(request, 'chat/chat_home.html', {
        'users': users, 
        'rooms': room_data,
        'announcements': announcements,
        'current_user_id': request.user.id
    })

@login_required
def create_direct_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    existing_rooms = Room.objects.filter(type='DIRECT', members=request.user).filter(members=target_user)
    
    if existing_rooms.exists():
        room = existing_rooms.first()
    else:
        room = Room.objects.create(type='DIRECT')
        room.members.add(request.user, target_user)
    
    return JsonResponse({'status': 'ok', 'room_id': room.id, 'room_name': f"{target_user.last_name} {target_user.first_name}"})

@login_required
def create_group_chat(request):
    if request.method == 'POST':
        # API này nhận JSON
        try:
            data = json.loads(request.body)
            group_name = data.get('group_name')
            member_ids = data.get('members', []) 
            
            if group_name and member_ids:
                room = Room.objects.create(name=group_name, type='GROUP')
                room.members.add(request.user) 
                room.admins.add(request.user)  
                
                for uid in member_ids:
                    try:
                        u = User.objects.get(id=uid)
                        room.members.add(u)
                    except User.DoesNotExist:
                        pass
                
                return JsonResponse({'status': 'ok', 'room_id': room.id})
        except:
            pass
            
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_member_to_group(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            room = Room.objects.get(id=room_id, type='GROUP')
            if request.user in room.admins.all():
                user_to_add = User.objects.get(id=user_id)
                room.members.add(user_to_add)
                return JsonResponse({'status': 'ok', 'message': f'Đã thêm {user_to_add.username}'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Bạn không phải trưởng nhóm'}, status=403)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

# --- API LẤY TIN NHẮN (CẬP NHẬT) ---
@login_required
def get_room_messages(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.user not in room.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    messages = room.messages.select_related('sender', 'parent').order_by('timestamp')
    
    data = []
    for msg in messages:
        parent_data = None
        if msg.parent:
            parent_data = {
                'id': msg.parent.id,
                'content': msg.parent.content[:50] + "..." if msg.parent.content else "Tin nhắn đính kèm",
                'sender': msg.parent.sender.last_name or msg.parent.sender.username
            }

        # Xử lý File/Ảnh
        file_url = None
        is_image = False
        file_name = ""
        
        if msg.attachment:
            file_url = msg.attachment.url
            file_name = os.path.basename(msg.attachment.name)
            ext = os.path.splitext(file_name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                is_image = True

        data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': f"{msg.sender.last_name} {msg.sender.first_name}",
            'avatar': msg.sender.username[0].upper(),
            'content': msg.content,
            'file_url': file_url,   # [MỚI]
            'is_image': is_image,   # [MỚI]
            'file_name': file_name, # [MỚI]
            'time': msg.timestamp.strftime('%H:%M %d/%m'),
            'is_me': msg.sender == request.user,
            'parent': parent_data
        })
    return JsonResponse(data, safe=False)

# --- API GỬI TIN NHẮN (CẬP NHẬT GỬI FILE) ---
@login_required
def send_message(request):
    if request.method == 'POST':
        # [CẬP NHẬT] Dùng POST thường thay vì JSON để nhận File
        room_id = request.POST.get('room_id')
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        attachment = request.FILES.get('attachment') # Lấy file
        
        if room_id:
            room = get_object_or_404(Room, id=room_id)
            if request.user not in room.members.all():
                return JsonResponse({'status': 'error', 'message': 'Not in room'}, status=403)

            parent_msg = None
            if parent_id:
                try:
                    parent_msg = Message.objects.get(id=parent_id)
                except Message.DoesNotExist:
                    pass

            processed_file = None
            
            # [CẬP NHẬT] Xử lý file nếu có
            if attachment:
                # Chặn file > 10MB
                if attachment.size > 10 * 1024 * 1024:
                    return JsonResponse({'status': 'error', 'message': 'File quá lớn (>10MB)'}, status=400)

                # Gọi hàm nén ảnh
                processed_file, error = process_image(attachment)
                if error:
                    return JsonResponse({'status': 'error', 'message': error}, status=400)

            # Chỉ tạo khi có nội dung hoặc file
            if content or processed_file:
                Message.objects.create(
                    room=room, 
                    sender=request.user, 
                    content=content, 
                    parent=parent_msg,
                    attachment=processed_file # Lưu file đã nén
                )
                
                room.save() # Update time
                return JsonResponse({'status': 'ok'})
            
    return JsonResponse({'status': 'error'}, status=400)

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