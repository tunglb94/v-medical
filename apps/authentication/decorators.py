from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            # 1. Luôn cho phép Admin/Superuser
            if request.user.is_superuser or request.user.role == 'ADMIN':
                return view_func(request, *args, **kwargs)
            
            # 2. Kiểm tra xem vai trò của user có nằm trong danh sách cho phép không
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                # SỬA LẠI TRANG BÁO LỖI: Thêm nút Đăng xuất để thoát vòng lặp
                role_display = request.user.get_role_display()
                return HttpResponseForbidden(f"""
                    <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif;'>
                        <h1 style='color: #e74a3b; margin-bottom: 20px;'>🚫 BẠN KHÔNG CÓ QUYỀN TRUY CẬP!</h1>
                        <p>Vai trò hiện tại của bạn: <strong>{role_display}</strong> ({request.user.role})</p>
                        <p>Trang này chỉ dành cho: {', '.join(allowed_roles)}</p>
                        
                        <div style='margin-top: 30px;'>
                            <a href='/' style='text-decoration: none; padding: 10px 20px; background-color: #4e73df; color: white; border-radius: 5px; margin-right: 10px;'>
                                Quay lại Trang chủ
                            </a>
                            <a href='/auth/logout/' style='text-decoration: none; padding: 10px 20px; background-color: #858796; color: white; border-radius: 5px;'>
                                Đăng xuất ngay
                            </a>
                        </div>
                    </div>
                """)
        return wrapper_func
    return decorator