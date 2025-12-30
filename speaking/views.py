from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import SpeakingTopic, SpeakingSentence, PronunciationLog
from django.contrib.auth.decorators import login_required
# Trang 1: Danh sách Topic
def topic_list(request):
    topics = SpeakingTopic.objects.all().order_by('-created_at')
    return render(request, 'speaking/topic_list.html', {'topics': topics})

# Trang 2: Danh sách Câu trong Topic
def sentence_list(request, topic_id):
    topic = get_object_or_404(SpeakingTopic, id=topic_id)
    sentences = topic.sentences.all()
    return render(request, 'speaking/sentence_list.html', {'topic': topic, 'sentences': sentences})

# Trang 3: Phòng luyện tập (Chứa cả logic trang 4)
def practice_sentence(request, sentence_id):
    sentence = get_object_or_404(SpeakingSentence, id=sentence_id)
    # Tìm câu tiếp theo
    next_sentence = SpeakingSentence.objects.filter(topic=sentence.topic, id__gt=sentence.id).first()
    return render(request, 'speaking/practice.html', {
        'sentence': sentence, 
        'next_sentence': next_sentence
    })

# API xử lý ghi âm (Gọi từ AJAX)

    
@login_required
def toggle_save_topic(request, topic_id):
    topic = get_object_or_404(SpeakingTopic, id=topic_id)
    user = request.user
    
    if user in topic.users_who_saved.all():
        topic.users_who_saved.remove(user)
        saved = False
    else:
        topic.users_who_saved.add(user)
        saved = True
        
    return JsonResponse({
        'status': 'success',
        'saved': saved
    })
@login_required
def saved_topics(request):
    topics = request.user.saved_speaking_topics.all().order_by('-created_at')
    return render(request, 'speaking/saved_topics.html', {'topics': topics})