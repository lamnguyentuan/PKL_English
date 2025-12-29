from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json

from .models import Topic, Flashcard
from .services.study_service import StudyService


# ===== Helpers =====
def public_topics_qs():
    """
    Topic hệ thống/public: owner=None + is_public=True
    (Tránh lộ topic riêng của user khác)
    """
    return Topic.objects.filter(owner__isnull=True, is_public=True)


# ===== Web pages =====
def index(request):
    topics = public_topics_qs().order_by("-id")
    context = {'topics': topics}
    return render(request, 'index.html', context)


@login_required
def topic_list(request):
    """Display list of PUBLIC topics with user's progress"""
    topics = public_topics_qs().order_by("-id")
    topics_with_progress = []

    for topic in topics:
        total_vocab = topic.vocabularies.count()
        if total_vocab > 0:
            mastered = Flashcard.objects.filter(
                user=request.user,
                vocabulary__topic=topic,
                mastery_level__gte=3
            ).count()
            progress = int((mastered / total_vocab) * 100)
        else:
            progress = 0

        topic.progress = progress
        topics_with_progress.append(topic)

    return render(request, 'study/topic_list.html', {'topics': topics_with_progress})



@login_required
def study_session(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    is_public = (topic.owner is None and topic.is_public)
    is_owner = (topic.owner_id == request.user.id)

    if not (is_public or is_owner):
        return render(request, 'study/finished.html', {
            'message': 'Topic không tồn tại hoặc bạn không có quyền truy cập.',
            'stats': StudyService.get_stats(request.user),
            'topic_id': topic_id
        })

    session_key = f'studied_cards_{topic_id}'
    studied_cards = request.session.get(session_key, [])

    card = StudyService.get_learning_card(request.user, topic_id, excluded_card_ids=studied_cards)

    if not card:
        if session_key in request.session:
            del request.session[session_key]
        stats = StudyService.get_stats(request.user)
        return render(request, 'study/finished.html', {
            'message': 'Bạn đã hoàn thành tất cả thẻ trong chủ đề này!',
            'stats': stats,
            'topic_id': topic_id
        })

    total_cards = StudyService.count_cards_to_learn(request.user, topic_id)
    session_progress = int((len(studied_cards) / total_cards) * 100) if total_cards > 0 else 0

    question_data = StudyService.generate_question_data(card)
    return render(request, 'study/study_page.html', {
        'question': question_data,
        'topic_id': topic_id,
        'progress': session_progress
    })


# ===== JSON endpoints (web AJAX, giữ nguyên) =====
@login_required
def submit_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        card_id = data.get('card_id')
        topic_id = data.get('topic_id')

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
    stats = StudyService.get_detailed_stats(request.user)
    return render(request, 'study/detailed_stats.html', {'stats': stats})


@login_required
def notebook(request):
    entries = StudyService.get_notebook(request.user)
    return render(request, 'study/notebook.html', {'entries': entries})


@login_required
def add_to_notebook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        note = data.get('note', '')
        result = StudyService.add_to_notebook(request.user, vocab_id, note)
        return JsonResponse(result)


@login_required
def remove_from_notebook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        result = StudyService.remove_from_notebook(request.user, vocab_id)
        return JsonResponse(result)


@login_required
def update_notebook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        note = data.get('note', '')
        result = StudyService.update_notebook_note(request.user, vocab_id, note)
        return JsonResponse(result)


@login_required
def reset_topic(request, topic_id):
    # ✅ chỉ reset public topic
    if not public_topics_qs().filter(id=topic_id).exists():
        return redirect('topic_list')

    StudyService.reset_topic_progress(request.user, topic_id)
    return redirect('study_session', topic_id=topic_id)


@login_required
def notebook_review(request):
    total_reviewable = StudyService.count_notebook_reviewable(request.user)
    if total_reviewable < 2:
        return render(request, 'study/notebook_review.html', {
            'error': 'Cần ít nhất 2 từ có audio trong sổ tay để ôn tập!'
        })

    session_key = 'notebook_reviewed'
    is_continuing = request.GET.get('continue', False)
    if not is_continuing:
        if session_key in request.session:
            del request.session[session_key]

    reviewed_ids = request.session.get(session_key, [])
    question = StudyService.get_notebook_review_question(request.user, excluded_vocab_ids=reviewed_ids)

    if not question:
        if session_key in request.session:
            del request.session[session_key]
        return render(request, 'study/notebook_review.html', {
            'finished': True,
            'total_reviewed': len(reviewed_ids)
        })

    progress = int((len(reviewed_ids) / total_reviewable) * 100) if total_reviewable > 0 else 0

    return render(request, 'study/notebook_review.html', {
        'question': question,
        'progress': progress,
        'current': len(reviewed_ids) + 1,
        'total': total_reviewable
    })


@login_required
def notebook_review_submit(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        vocab_id = data.get('vocabulary_id')
        question_type = data.get('question_type', 'listening')

        session_key = 'notebook_reviewed'
        reviewed_ids = request.session.get(session_key, [])
        if int(vocab_id) not in reviewed_ids:
            reviewed_ids.append(int(vocab_id))
            request.session[session_key] = reviewed_ids

        if question_type == 'fill_blank':
            user_answer = data.get('user_answer', '')
            result = StudyService.check_fill_blank_review(vocab_id, user_answer)
        else:
            selected_id = data.get('selected_id')
            result = StudyService.check_review_answer(vocab_id, selected_id)

        return JsonResponse(result)


@login_required
def notebook_review_reset(request):
    session_key = 'notebook_reviewed'
    if session_key in request.session:
        del request.session[session_key]
    return redirect('notebook_review')

from django.contrib import messages
from django.shortcuts import get_object_or_404
from .forms import MyTopicForm, MyVocabularyForm
from .models import Vocabulary

@login_required
def my_topic_list(request):
    topics = Topic.objects.filter(owner=request.user).order_by("-id")
    return render(request, "study/my_topic_list.html", {"topics": topics})

@login_required
def my_topic_create(request):
    if request.method == "POST":
        form = MyTopicForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.owner = request.user
            topic.is_public = False
            topic.save()
            messages.success(request, "Đã tạo Topic riêng.")
            return redirect("my_topic_detail", topic_id=topic.id)
        messages.error(request, "Tạo Topic thất bại.")
    else:
        form = MyTopicForm()
    return render(request, "study/my_topic_form.html", {"form": form, "mode": "create"})

@login_required
def my_topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
    vocabs = Vocabulary.objects.filter(topic=topic).order_by("id")
    return render(request, "study/my_topic_detail.html", {"topic": topic, "vocabs": vocabs})

@login_required
def my_topic_edit(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
    if request.method == "POST":
        form = MyTopicForm(request.POST, request.FILES, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật Topic.")
            return redirect("my_topic_detail", topic_id=topic.id)
        messages.error(request, "Cập nhật thất bại.")
    else:
        form = MyTopicForm(instance=topic)
    return render(request, "study/my_topic_form.html", {"form": form, "mode": "edit"})

@login_required
def my_topic_delete(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
    if request.method == "POST":
        topic.delete()
        messages.success(request, "Đã xóa Topic.")
        return redirect("my_topic_list")
    return render(request, "study/my_topic_delete.html", {"topic": topic})

@login_required
def my_vocab_create(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
    if request.method == "POST":
        form = MyVocabularyForm(request.POST, request.FILES)
        if form.is_valid():
            vocab = form.save(commit=False)
            vocab.topic = topic
            vocab.save()
            messages.success(request, "Đã thêm từ vựng.")
            return redirect("my_topic_detail", topic_id=topic.id)
        messages.error(request, "Thêm từ thất bại.")
    else:
        form = MyVocabularyForm()
    return render(request, "study/my_vocab_form.html", {"form": form, "topic": topic, "mode": "create"})

@login_required
def my_vocab_edit(request, topic_id, vocab_id):
    topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
    vocab = get_object_or_404(Vocabulary, id=vocab_id, topic=topic)
    if request.method == "POST":
        form = MyVocabularyForm(request.POST, request.FILES, instance=vocab)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật từ vựng.")
            return redirect("my_topic_detail", topic_id=topic.id)
        messages.error(request, "Cập nhật thất bại.")
    else:
        form = MyVocabularyForm(instance=vocab)
    return render(request, "study/my_vocab_form.html", {"form": form, "topic": topic, "mode": "edit"})

@login_required
def my_vocab_delete(request, topic_id, vocab_id):
    topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
    vocab = get_object_or_404(Vocabulary, id=vocab_id, topic=topic)
    if request.method == "POST":
        vocab.delete()
        messages.success(request, "Đã xóa từ vựng.")
        return redirect("my_topic_detail", topic_id=topic.id)
    return render(request, "study/my_vocab_delete.html", {"topic": topic, "vocab": vocab})

