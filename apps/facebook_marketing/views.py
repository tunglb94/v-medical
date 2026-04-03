from django.shortcuts import render
from django.http import JsonResponse
from .models import FacebookPage, FacebookPostLog
from .fb_service import FBGraphService
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import datetime
import traceback  # <-- THƯ VIỆN ĐỂ IN LỖI CHI TIẾT TỚI TỪNG DÒNG (TRACEBACK)
import json       # <-- THƯ VIỆN ĐỂ IN KẾT QUẢ TỪ FACEBOOK CHO DỄ ĐỌC

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
            
            # -------------------------------------------------------------
            # 1. IN LOG CHI TIẾT NHỮNG GÌ BẠN ĐANG GỬI LÊN FB
            # -------------------------------------------------------------
            print("\n" + "="*70)
            print("🚀 [AUTO POST FB] ĐANG GỬI YÊU CẦU...")
            print(f"👉 Fanpage ID : {page_id}")
            print(f"👉 Nội dung   : {content}")
            print(f"👉 Hẹn giờ    : {schedule_time} (Unix: {unix_schedule_time})")
            print(f"👉 Đính kèm   : {len(files)} file")
            for idx, f in enumerate(files):
                print(f"   - File {idx+1}: {f.name} (Type: {f.content_type}, Size: {f.size} bytes)")
            print("-" * 70)
            
            # TRUYỀN unix_schedule_time vào Service
            res = service.post_to_facebook(content, files, scheduled_time=unix_schedule_time)
            
            # -------------------------------------------------------------
            # 2. IN NGUYÊN VĂN PHẢN HỒI TỪ FACEBOOK 
            # (Giúp phát hiện "báo thành công nhưng là ảo")
            # -------------------------------------------------------------
            print("📬 [AUTO POST FB] KẾT QUẢ TỪ FACEBOOK TRẢ VỀ:")
            print(json.dumps(res, indent=4, ensure_ascii=False))
            print("="*70 + "\n")
            
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
            # -------------------------------------------------------------
            # 3. TRACEBACK: IN LỖI CHI TIẾT TỪNG DÒNG CODE NẾU BỊ CRASH
            # -------------------------------------------------------------
            print("\n" + "="*70)
            print("❌ [AUTO POST FB] HỆ THỐNG BỊ LỖI (CRASH):")
            print(traceback.format_exc()) # Hàm này in ra dòng code nào gây lỗi
            print("="*70 + "\n")
            
            return JsonResponse({
                'error': {
                    'message': str(e), 
                    'details': "Hãy xem log Server để biết lỗi chi tiết."
                }
            }, status=500)
            
    return JsonResponse({'error': {'message': 'Invalid Method'}}, status=405)