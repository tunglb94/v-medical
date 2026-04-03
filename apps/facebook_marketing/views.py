from django.shortcuts import render
from django.http import JsonResponse
from .models import FacebookPage, FacebookPostLog
from .fb_service import FBGraphService
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import datetime

@login_required
def facebook_autopost_view(request):
    # Lấy tất cả page đang active (Tất cả nhân viên đều thấy)
    pages = FacebookPage.objects.filter(is_active=True)
    recent_logs = FacebookPostLog.objects.filter(staff=request.user)[:10]
    return render(request, 'marketing/fb_autopost.html', {'pages': pages, 'recent_logs': recent_logs})

@csrf_exempt
@login_required
def api_post_fb(request):
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        content = request.POST.get('content')
        schedule_time = request.POST.get('schedule_time') # <-- Lấy giờ từ HTML
        files = request.FILES.getlist('images')
        
        # Chuyển đổi giờ HTML sang Unix Timestamp cho Facebook
        unix_schedule_time = None
        if schedule_time:
            try:
                dt = datetime.datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")
                unix_schedule_time = int(dt.timestamp())
            except ValueError:
                pass
        
        try:
            page = FacebookPage.objects.get(page_id=page_id, is_active=True)
            service = FBGraphService(page.page_id, page.access_token)
            
            for f in files: f.seek(0)
            
            # TRUYỀN unix_schedule_time vào Service
            res = service.post_to_facebook(content, files, scheduled_time=unix_schedule_time)
            
            # LƯU LOG VÀO DATABASE
            status = 'Success' if 'id' in res else 'Failed'
            err = res.get('error', {}).get('message', '') if 'error' in res else ''
            
            FacebookPostLog.objects.create(
                page=page,
                staff=request.user,
                content=content[:500],
                status=status,
                post_id=res.get('id', ''),
                error_message=err
            )
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({'error': {'message': str(e)}}, status=500)
            
    return JsonResponse({'error': {'message': 'Invalid Method'}}, status=405)