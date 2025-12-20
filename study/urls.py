from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 1. Trang danh sách chủ đề (Trang chủ của app study)
    # URL: /study/
    path('', views.topic_list, name='topic_list'),

    # 2. Trang làm bài tập (Học theo Topic)
    # URL: /study/1/ (Học topic có ID là 1)
    path('<int:topic_id>/', views.study_session, name='study_session'),

    # 3. API nhận đáp án (Dùng cho AJAX gửi lên, không phải trang để người dùng vào)
    # URL: /study/api/submit-answer/
    path('submit_answer/', views.submit_answer, name='submit_answer'),

    # 4. Trang thống kê
    # URL: /study/dashboard/
    path('dashboard/', views.study_stats, name='dashboard'),
]