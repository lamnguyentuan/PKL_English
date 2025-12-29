from django.urls import path
from . import views

urlpatterns = [
    # ===== MY TOPICS UI (demo) =====
    path('my-topics/', views.my_topic_list, name='my_topic_list'),
    path('my-topics/create/', views.my_topic_create, name='my_topic_create'),
    path('my-topics/<int:topic_id>/', views.my_topic_detail, name='my_topic_detail'),
    path('my-topics/<int:topic_id>/edit/', views.my_topic_edit, name='my_topic_edit'),
    path('my-topics/<int:topic_id>/delete/', views.my_topic_delete, name='my_topic_delete'),

    path('my-topics/<int:topic_id>/vocab/create/', views.my_vocab_create, name='my_vocab_create'),
    path('my-topics/<int:topic_id>/vocab/<int:vocab_id>/edit/', views.my_vocab_edit, name='my_vocab_edit'),
    path('my-topics/<int:topic_id>/vocab/<int:vocab_id>/delete/', views.my_vocab_delete, name='my_vocab_delete'),

    # ===== STUDY (cũ) =====
    path('', views.topic_list, name='topic_list'),
    path('submit_answer/', views.submit_answer, name='submit_answer'),
    path('dashboard/', views.study_stats, name='dashboard'),
    path('stats/', views.detailed_stats, name='detailed_stats'),

    path('notebook/', views.notebook, name='notebook'),
    path('notebook/add/', views.add_to_notebook, name='add_to_notebook'),
    path('notebook/remove/', views.remove_from_notebook, name='remove_from_notebook'),
    path('notebook/update/', views.update_notebook, name='update_notebook'),

    path('notebook/review/', views.notebook_review, name='notebook_review'),
    path('notebook/review/submit/', views.notebook_review_submit, name='notebook_review_submit'),
    path('notebook/review/reset/', views.notebook_review_reset, name='notebook_review_reset'),

    path('<int:topic_id>/reset/', views.reset_topic, name='reset_topic'),
    path('<int:topic_id>/', views.study_session, name='study_session'),
]
