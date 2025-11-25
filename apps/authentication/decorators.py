from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            # 1. Luôn cho phép Admin/Superuser
            if request.user.is_superuser or request.user.role == 'ADMIN':
                return view_func(request, *args, **kwargs)
            
            # 2. Kiểm tra xem vai trò của user có nằm trong danh sách cho phép không
            # user.role trả về chuỗi: 'TELESALE', 'RECEPTIONIST', 'DOCTOR'...
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("""
                    <h1 style='color: red; text-align: center; margin-top: 50px;'>
                        BẠN KHÔNG CÓ QUYỀN TRUY CẬP TRANG NÀY! 🚫
                    </h1>
                    <p style='text-align: center;'><a href='/'>Quay lại trang chủ</a></p>
                """)
        return wrapper_func
    return decorator