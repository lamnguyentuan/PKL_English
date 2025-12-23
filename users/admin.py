from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Cách an toàn để hủy đăng ký User mặc định
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    # Nếu User chưa được đăng ký thì bỏ qua, không báo lỗi gây sập app
    pass

# Đăng ký lại User với giao diện tùy chỉnh của bạn
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Bạn có thể thêm các cột muốn hiển thị ở đây
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    # Các cấu hình khác giữ nguyên từ UserAdmin mặc định