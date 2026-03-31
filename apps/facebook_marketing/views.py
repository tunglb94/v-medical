from django.shortcuts import render
from django.http import JsonResponse
from .models import FacebookPage, FacebookPostLog
from .fb_service import FBGraphService
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
def facebook_autopost_view(request):
    pages = FacebookPage.objects.filter(allowed_staff=request.user, is_active=True)
    # Lấy 10 log gần nhất của nhân viên này để hiển thị trên giao diện
    recent_logs = FacebookPostLog.objects.filter(staff=request.user)[:10]
    return render(request, 'marketing/fb_autopost.html', {'pages': pages, 'recent_logs': recent_logs})

@csrf_exempt
@login_required
def api_post_fb(request):
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        content = request.POST.get('content')
        files = request.FILES.getlist('images')
        
        try:
            page = FacebookPage.objects.get(page_id=page_id, allowed_staff=request.user)
            service = FBGraphService(page.page_id, page.access_token)
            
            for f in files: f.seek(0)
            res = service.post_to_facebook(content, files)
            
            # LƯU LOG VÀO DATABASE
            status = 'Success' if 'id' in res else 'Failed'
            err = res.get('error', {}).get('message', '') if 'error' in res else ''
            
            FacebookPostLog.objects.create(
                page=page,
                staff=request.user,
                content=content[:500], # Lưu ngắn gọn để check
                status=status,
                post_id=res.get('id', ''),
                error_message=err
            )
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({'error': {'message': str(e)}}, status=500)
            
    return JsonResponse({'error': {'message': 'Invalid Method'}}, status=405)