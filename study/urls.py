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
    
    # Thống kê chi tiết
    path('stats/', views.detailed_stats, name='detailed_stats'),

    # Sổ tay từ vựng
    path('notebook/', views.notebook, name='notebook'),
    path('notebook/add/', views.add_to_notebook, name='add_to_notebook'),
    path('notebook/remove/', views.remove_from_notebook, name='remove_from_notebook'),
    path('notebook/update/', views.update_notebook, name='update_notebook'),

    # Reset tiến độ topic
    path('<int:topic_id>/reset/', views.reset_topic, name='reset_topic'),

    # Ôn tập sổ tay
    path('notebook/review/', views.notebook_review, name='notebook_review'),
    path('notebook/review/submit/', views.notebook_review_submit, name='notebook_review_submit'),
    path('notebook/review/reset/', views.notebook_review_reset, name='notebook_review_reset'),
]