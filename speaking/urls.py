from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views         # Chứa API (JSON)
from . import views_front   # Chứa HTML (Frontend)

# --- 1. CẤU HÌNH ROUTER API ---
# Router này tự động tạo các URL:
# - GET /api/speaking/topics/       (Lấy danh sách)
# - GET /api/speaking/topics/{id}/  (Lấy chi tiết + câu hỏi)
router = DefaultRouter()
router.register(r'api/speaking/topics', views.SpeakingTopicViewSet, basename='api-speaking-topic')

urlpatterns = [
    # =========================================
    # A. FRONTEND PATHS (Trả về HTML cho người dùng)
    # =========================================
    
    # 1. Trang danh sách chủ đề (Giao diện thẻ bài)
    path('speaking/', views_front.speaking_topic_list, name='speaking_topics'),
    
    # 2. Trang luyện tập (Giao diện ghi âm)
    # Lưu ý: Ta gộp luôn sentence_list vào đây nên chỉ cần 1 đường dẫn này
    path('speaking/<int:topic_id>/', views_front.speaking_practice, name='speaking_practice'),


    # =========================================
    # B. API PATHS (Trả về JSON cho Javascript)
    # =========================================
    
    # Nhúng các URL do Router sinh ra (Topics List & Detail)
    path('', include(router.urls)),
    
    # API Nộp bài ghi âm & Chấm điểm
    # URL: /api/speaking/submit/
    path('api/speaking/submit/', views.SubmitPronunciationView.as_view(), name='api-speaking-submit'),
]