from django.shortcuts import render, redirect
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
    # Lấy danh sách card đã học trong phiên từ session
    session_key = f'studied_cards_{topic_id}'
    studied_cards = request.session.get(session_key, [])
    
    # Lấy card tiếp theo (loại bỏ các card đã học)
    card = StudyService.get_learning_card(request.user, topic_id, excluded_card_ids=studied_cards)
    
    if not card:
        # Hết bài -> xóa session và hiển thị kết quả
        if session_key in request.session:
            del request.session[session_key]
        stats = StudyService.get_stats(request.user)
        return render(request, 'study/finished.html', {
            'message': 'Bạn đã hoàn thành tất cả thẻ trong chủ đề này!',
            'stats': stats,
            'topic_id': topic_id
        })
    
    # Tính progress trong phiên (số từ đã học / tổng số từ cần học)
    total_cards = StudyService.count_cards_to_learn(request.user, topic_id)
    session_progress = int((len(studied_cards) / total_cards) * 100) if total_cards > 0 else 0
    
    question_data = StudyService.generate_question_data(card)
    return render(request, 'study/study_page.html', {
        'question': question_data,
        'topic_id': topic_id,
        'progress': session_progress
    })

@login_required
def submit_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        card_id = data.get('card_id')
        topic_id = data.get('topic_id')
        
        # Lưu card_id vào session (đánh dấu đã học)
        if topic_id:
            session_key = f'studied_cards_{topic_id}'
            studied_cards = request.session.get(session_key, [])
            if int(card_id) not in studied_cards:
                studied_cards.append(int(card_id))
                request.session[session_key] = studied_cards

        result = StudyService.check_answer(request.user, card_id, data.get('user_answer'))
        return JsonResponse(result)

@login_required
def study_stats(request):
    stats = StudyService.get_stats(request.user)
    return render(request, 'study/dashboard.html', {'stats': stats})

@login_required
def detailed_stats(request):
    """Thống kê chi tiết"""
    stats = StudyService.get_detailed_stats(request.user)
    return render(request, 'study/detailed_stats.html', {'stats': stats})

@login_required
def notebook(request):
    """Hiển thị sổ tay từ vựng"""
    entries = StudyService.get_notebook(request.user)
    return render(request, 'study/notebook.html', {'entries': entries})

@login_required
def add_to_notebook(request):
    """API thêm từ vào sổ tay"""
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        note = data.get('note', '')
        result = StudyService.add_to_notebook(request.user, vocab_id, note)
        return JsonResponse(result)

@login_required
def remove_from_notebook(request):
    """API xóa từ khỏi sổ tay"""
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        result = StudyService.remove_from_notebook(request.user, vocab_id)
        return JsonResponse(result)

@login_required
def update_notebook(request):
    """API cập nhật ghi chú"""
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        note = data.get('note', '')
        result = StudyService.update_notebook_note(request.user, vocab_id, note)
        return JsonResponse(result)

@login_required
def reset_topic(request, topic_id):
    """Reset tiến độ học của 1 topic"""
    StudyService.reset_topic_progress(request.user, topic_id)
    return redirect('study_session', topic_id=topic_id)

@login_required
def notebook_review(request):
    """Ôn tập từ vựng trong sổ tay"""
    # Kiểm tra có đủ từ để ôn không
    total_reviewable = StudyService.count_notebook_reviewable(request.user)
    if total_reviewable < 2:
        return render(request, 'study/notebook_review.html', {
            'error': 'Cần ít nhất 2 từ có audio trong sổ tay để ôn tập!'
        })
    
    # Lấy danh sách từ đã ôn trong phiên
    session_key = 'notebook_reviewed'
    reviewed_ids = request.session.get(session_key, [])
    
    # Lấy câu hỏi tiếp theo
    question = StudyService.get_notebook_review_question(request.user, excluded_vocab_ids=reviewed_ids)
    
    if not question:
        # Hết câu hỏi -> xóa session
        if session_key in request.session:
            del request.session[session_key]
        return render(request, 'study/notebook_review.html', {
            'finished': True,
            'total_reviewed': len(reviewed_ids)
        })
    
    # Tính progress
    progress = int((len(reviewed_ids) / total_reviewable) * 100) if total_reviewable > 0 else 0
    
    return render(request, 'study/notebook_review.html', {
        'question': question,
        'progress': progress,
        'current': len(reviewed_ids) + 1,
        'total': total_reviewable
    })

@login_required
def notebook_review_submit(request):
    """API submit đáp án ôn tập"""
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        question_type = data.get('question_type', 'listening')
        
        # Lưu vào session
        session_key = 'notebook_reviewed'
        reviewed_ids = request.session.get(session_key, [])
        if int(vocab_id) not in reviewed_ids:
            reviewed_ids.append(int(vocab_id))
            request.session[session_key] = reviewed_ids
        
        # Kiểm tra đáp án theo loại câu hỏi
        if question_type == 'fill_blank':
            user_answer = data.get('user_answer', '')
            result = StudyService.check_fill_blank_review(vocab_id, user_answer)
        else:  # listening
            selected_id = data.get('selected_id')
            result = StudyService.check_review_answer(vocab_id, selected_id)
        
        return JsonResponse(result)

@login_required
def notebook_review_reset(request):
    """Reset phiên ôn tập"""
    session_key = 'notebook_reviewed'
    if session_key in request.session:
        del request.session[session_key]
    return redirect('notebook_review')


