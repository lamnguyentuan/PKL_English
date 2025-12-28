from django.urls import path
from django.contrib.auth import views as auth_views
from . import views         # Chứa API (JSON) - RegisterView, LoginView...
from . import views_front   # Chứa HTML (Frontend) - login_page, register_page

urlpatterns = [
    # =========================================
    # A. FRONTEND PATHS (Trả về HTML cho người dùng)
    # =========================================
    
    # 1. Trang Đăng ký (Render HTML users/register.html)
    path('register/', views_front.register_page, name='register'),

    # 2. Trang Đăng nhập (Render HTML users/login.html)
    path('login/', views_front.login_page, name='login'),

    # 3. Đăng xuất
    # Lưu ý: Với nút Đăng xuất trên Navbar, ta dùng luôn View có sẵn của Django 
    # để nó tự xử lý xóa session và chuyển hướng về trang chủ ('/') ngay lập tức.
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),


    # =========================================
    # B. API PATHS (Trả về JSON cho Javascript)
    # =========================================
    
    # API Đăng ký (JS gọi vào đây)
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    
    # API Đăng nhập (JS gọi vào đây)
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    
    # API Lấy thông tin user (Avatar, tên...)
    path('api/profile/', views.ProfileView.as_view(), name='api_profile'),
]