from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views         # Backend API
from . import views_front   # Frontend HTML

# Router cho API
router = DefaultRouter()
router.register(r'api/topics', views.TopicViewSet, basename='study-topic')

urlpatterns = [
    # --- PHẦN FRONTEND (Giao diện) ---
    
    # 1. Trang chủ (http://127.0.0.1:8000/)
    # Nếu bạn muốn trang chủ là trang giới thiệu (Landing page)
    path('', views_front.home_page, name='home'),

    # 2. Trang danh sách chủ đề (http://127.0.0.1:8000/study/)
    # QUAN TRỌNG: Phải thêm chữ 'study/' vào đây thì mới chạy được link /study/
    path('study/', views_front.study_topic_list, name='topic_list'),

    # 3. Trang học Flashcard (http://127.0.0.1:8000/study/flashcards/1/)
    path('study/flashcards/<int:topic_id>/', views_front.study_flashcards, name='study_flashcards'),

    # --- PHẦN API (Dữ liệu ngầm) ---
    # Bao gồm các link như: /api/topics/
    path('', include(router.urls)), 
]