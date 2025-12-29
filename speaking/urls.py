from django.urls import path
from . import views

# speaking/urls.py
urlpatterns = [
    path('topics/', views.topic_list, name='speaking_topics'), # Đổi ở đây
    path('topics/<int:topic_id>/', views.sentence_list, name='sentence_list'),
    path('practice/<int:sentence_id>/', views.practice_sentence, name='practice_sentence'),
    path('submit-audio/', views.submit_pronunciation, name='submit_pronunciation'),
    path('toggle-save/<int:topic_id>/', views.toggle_save_topic, name='toggle_save_topic'),
    path('topics/saved/', views.saved_topics, name='saved_topics'), 
]