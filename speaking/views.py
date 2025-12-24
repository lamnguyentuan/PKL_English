from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import SpeakingTopic, SpeakingSentence, PronunciationLog
from .services.services import AzureSpeechService

# Trang 1: Danh sách Topic
def topic_list(request):
    topics = SpeakingTopic.objects.all()
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
def submit_pronunciation(request):
    if request.method == 'POST':
        sentence_id = request.POST.get('sentence_id')
        audio_data = request.FILES.get('audio_data')
        sentence = get_object_or_404(SpeakingSentence, id=sentence_id)

        # Tạo log tạm để lấy file vật lý
        log = PronunciationLog.objects.create(
            user=request.user,
            sentence=sentence,
            audio_file=audio_data
        )

        # Gọi Azure
        result = AzureSpeechService.assess_pronunciation(log.audio_file.path, sentence.text)

        if result['success']:
            log.overall_score = result['overall_score']
            log.accuracy_score = result['accuracy_score']
            log.fluency_score = result['fluency_score']
            log.completeness_score = result['completeness_score']
            log.api_response = result['full_response']
            log.save()
            return JsonResponse({"status": "success", "data": result})
        
        return JsonResponse({"status": "error", "message": "API Error"}, status=500)