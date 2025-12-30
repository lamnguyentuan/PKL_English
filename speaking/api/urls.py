from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.api_topic_list, name='api_topic_list'),
    path('sentences/<int:topic_id>/', views.api_sentence_list, name='api_sentence_list'),
    path('practice/<int:sentence_id>/', views.api_practice_detail, name='api_practice_detail'),
    path('submit-audio/', views.api_submit_pronunciation, name='api_submit_pronunciation'),
    path('toggle-save/<int:topic_id>/', views.api_toggle_save_topic, name='api_toggle_save_topic'),
    path('saved-topics/', views.api_saved_topics, name='api_saved_topics'),
]