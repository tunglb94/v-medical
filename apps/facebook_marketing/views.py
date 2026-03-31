from django.shortcuts import render
from django.http import JsonResponse
from .models import FacebookPage
from .fb_service import FBGraphService
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
def facebook_autopost_view(request):
    # Giao diện chính: Lấy các Fanpage mà nhân viên này được cấp quyền
    pages = FacebookPage.objects.filter(allowed_staff=request.user, is_active=True)
    return render(request, 'marketing/fb_autopost.html', {'pages': pages})

@csrf_exempt # Cho phép gọi API từ Javascript
@login_required
def api_post_fb(request):
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        content = request.POST.get('content')
        files = request.FILES.getlist('images') # Lưu ý: HTML đang gửi name='images'
        
        try:
            page = FacebookPage.objects.get(page_id=page_id, allowed_staff=request.user)
            service = FBGraphService(page.page_id, page.access_token)
            
            # Đảm bảo con trỏ file ở vị trí 0
            for f in files: f.seek(0)
            
            res = service.post_to_facebook(content, files)
            return JsonResponse(res)
        except FacebookPage.DoesNotExist:
            return JsonResponse({'error': 'Page không tồn tại hoặc bạn không có quyền'}, status=403)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)