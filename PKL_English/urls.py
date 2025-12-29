from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from study.views import index  # chỉ cần index cho trang home

admin.site.site_header = "Hệ thống quản lý PKL English"
admin.site.site_title = "PKL English Admin Portal"
admin.site.index_title = "Chào mừng đến với trang quản trị nội dung"

urlpatterns = [
    path("admin/", admin.site.urls),

    # WEB (HTML render) - giữ nguyên để không gãy hệ thống
    path("", index, name="home"),
    path("", include("users.urls")),
    path("study/", include("study.urls")),
    path("speaking/", include("speaking.urls")),

    # API (REST)
    path("api/v1/", include("PKL_English.urls_api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
