from django.shortcuts import render
from django.http import JsonResponse
from .models import FacebookPage
from .fb_service import FBGraphService
from django.contrib.auth.decorators import login_required

@login_required
def facebook_autopost_view(request):
    # Lấy ra các Fanpage mà nhân viên này được cấp quyền
    pages = FacebookPage.objects.filter(allowed_staff=request.user, is_active=True)
    
    if request.method == 'POST':
        page_ids = request.POST.getlist('pages[]')
        content = request.POST.get('content')
        files = request.FILES.getlist('images[]')
        
        results = []
        selected_pages = FacebookPage.objects.filter(page_id__in=page_ids)
        
        for page in selected_pages:
            service = FBGraphService(page.page_id, page.access_token)
            for f in files: f.seek(0) # Đặt lại con trỏ file ảnh để đăng cho page tiếp theo
            res = service.post_to_facebook(content, files)
            results.append({'page': page.name, 'result': res})
            
        return JsonResponse({'status': 'done', 'results': results})

    return render(request, 'marketing/fb_autopost.html', {'pages': pages})