"""
URL configuration for PKL_English project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. Import view của trang chủ từ app Study
from study import views_front as study_views

admin.site.site_header = "Hệ thống quản lý PKL English"
admin.site.site_title = "PKL English Admin Portal"
admin.site.index_title = "Chào mừng đến với trang quản trị nội dung"

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- ƯU TIÊN SỐ 1: TRANG CHỦ ---
    # Đặt dòng này lên đầu để chắc chắn vào '/' là ra trang web, không ra API
    path('', study_views.home_page, name='home'),

    # --- CÁC APP KHÁC ---
    # (Thứ tự dưới này không còn quá quan trọng với trang chủ nữa)
    path('', include('users.urls')),
    path('', include('speaking.urls')),
    
    # Study App (Chứa các link con như /study/..., /api/topics/...)
    path('', include('study.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)