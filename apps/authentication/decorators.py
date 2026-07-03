from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def allowed_users(allowed_roles=[]):
    """
    Decorator kiểm tra quyền truy cập.
    Ưu tiên 1: Checkbox quyền (allowed_menus).
    Ưu tiên 2: Role cũ (Fallback).
    """
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            user = request.user
            
            # 1. Admin/Superuser luôn được phép
            if user.is_superuser or user.role == 'ADMIN':
                return view_func(request, *args, **kwargs)

            # 2. TỰ ĐỘNG CHECK QUYỀN DỰA TRÊN TÊN APP (MODULE)
            # Lấy tên app từ đường dẫn view (VD: 'apps.telesales.views' -> app_name='telesales')
            module_name = view_func.__module__
            app_name = "unknown"
            
            if "apps." in module_name:
                try:
                    # Cấu trúc apps.ten_app.views -> lấy 'ten_app'
                    app_name = module_name.split('.')[1]
                except:
                    pass

            # Bảng map giữa Tên App (Folder) và Key Menu (trong Database/Form)
            # Key bên trái là tên thư mục app, Key bên phải là tên trong MENU_CHOICES
            app_permission_map = {
                'telesales': 'telesale',       # App telesales cần quyền 'telesale'
                'reception': 'reception',      # App reception cần quyền 'reception'
                'marketing': 'marketing',      # App marketing cần quyền 'marketing'
                'customers': 'customers',      # App customers cần quyền 'customers'
                'sales': 'sales_report',       # App sales (báo cáo) cần quyền 'sales_report'
                'inventory': 'inventory',      # App inventory cần quyền 'inventory'
                'hr': 'hr',                    # App hr cần quyền 'hr'
                'clinical_portal': 'clinical_portal',  # App clinical_portal cần quyền 'clinical_portal'
            }

            required_permission = app_permission_map.get(app_name)

            # Nếu xác định được quyền cần thiết và User có quyền đó -> CHO QUA
            if required_permission and user.has_menu_access(required_permission):
                return view_func(request, *args, **kwargs)

            # 3. (Fallback) Nếu chưa tích checkbox, kiểm tra theo Role cũ (để hệ thống không bị gãy ngay lập tức)
            if user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # 4. Từ chối truy cập
            role_display = user.get_role_display()
            return HttpResponseForbidden(f"""
                <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; text-align: center;'>
                    <h1 style='color: #e74a3b; margin-bottom: 20px;'>🚫 BẠN KHÔNG CÓ QUYỀN TRUY CẬP!</h1>
                    <p>Tài khoản: <strong>{user.username}</strong> - Vai trò: <strong>{role_display}</strong></p>
                    <p style='color: #555;'>Bạn chưa được cấp quyền truy cập chức năng này (Checkbox: <strong>{required_permission}</strong>).</p>
                    <p>Vui lòng liên hệ Admin để vào trang "Quản lý nhân sự" và tích chọn quyền cho bạn.</p>
                    <div style='margin-top: 30px;'>
                        <a href='/' style='text-decoration: none; padding: 10px 20px; background-color: #4e73df; color: white; border-radius: 5px; margin-right: 10px;'>Về Trang chủ</a>
                        <a href='/auth/logout/' style='text-decoration: none; padding: 10px 20px; background-color: #858796; color: white; border-radius: 5px;'>Đăng xuất</a>
                    </div>
                </div>
            """)
            
        return wrapper_func
    return decorator