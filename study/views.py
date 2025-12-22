from django.shortcuts import render
from django.http import JsonResponse
from .models import Topic, Flashcard
from django.contrib.auth.decorators import login_required
import json
from .services.study_service import StudyService
# Create your views here.

def index(request):
    topics = Topic.objects.all()
    context = {'topics': topics}
    return render(request, 'index.html', context)

@login_required
def topic_list(request):
    """Display list of topics with user's progress"""
    topics = Topic.objects.all()
    topics_with_progress = []
    
    for topic in topics:
        # Calculate progress for each topic
        total_vocab = topic.vocabularies.count()
        if total_vocab > 0:
            mastered = Flashcard.objects.filter(
                user=request.user,
                vocabulary__topic=topic,
                mastery_level__gte=3  # Consider mastered at level 3+
            ).count()
            progress = int((mastered / total_vocab) * 100)
        else:
            progress = 0
        
        # Add progress as an attribute to the topic object
        topic.progress = progress
        topics_with_progress.append(topic)
    
    return render(request, 'study/topic_list.html', {'topics': topics_with_progress}) 

@login_required
def study_session(request, topic_id):
    card = StudyService.get_learning_card(request.user, topic_id)
    if not card:
        return render(request, 'study/finished.html', {'message': 'Bạn đã hoàn thành tất cả thẻ trong chủ đề này!'})
    question_data = StudyService.generate_question_data(card)
    return render(request, 'study/study_page.html', {
        'question': question_data,
        'topic_id': topic_id
        })

@login_required
def submit_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        result = StudyService.check_answer(request.user, data.get('card_id'), data.get('user_answer'))
        return JsonResponse(result)

@login_required
def study_stats(request):
    stats = StudyService.get_stats(request.user)
    return render(request, 'study/dashboard.html', {'stats': stats})

