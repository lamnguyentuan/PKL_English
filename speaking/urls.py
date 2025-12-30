from django.urls import path, include
from . import views

urlpatterns = [
    # Giao diện HTML
    # SỬA: Đổi name='topic_list' thành name='speaking_topics'
    path('topics/', views.topic_list, name='speaking_topics'), 
    
    path('saved/', views.saved_topics, name='saved_topics'),
    path('sentences/<int:topic_id>/', views.sentence_list, name='sentence_list'),
    path('practice/<int:sentence_id>/', views.practice_sentence, name='practice_sentence'),

    # Kết nối bộ API
    path('api/', include('speaking.api.urls')), 
]