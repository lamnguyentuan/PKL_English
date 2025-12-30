import time
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

# Dùng 2 dấu chấm (..) để lấy Model từ thư mục cha
from ..models import SpeakingTopic, SpeakingSentence, PronunciationLog
from .serializers import (
    SpeakingTopicSerializer, 
    SpeakingSentenceSerializer, 
    PronunciationLogSerializer
)
# Dùng 2 dấu chấm (..) để lấy Services từ thư mục cha
from ..services.services import AzureSpeechService

# API 1: Lấy danh sách Topic
@api_view(['GET'])
@permission_classes([AllowAny])
def api_topic_list(request):
    topics = SpeakingTopic.objects.all().order_by('-created_at')
    serializer = SpeakingTopicSerializer(topics, many=True, context={'request': request})
    return Response(serializer.data)

# API 2: Lấy danh sách câu trong một Topic
@api_view(['GET'])
@permission_classes([AllowAny])
def api_sentence_list(request, topic_id):
    topic = get_object_or_404(SpeakingTopic, id=topic_id)
    sentences = topic.sentences.all()
    serializer = SpeakingSentenceSerializer(sentences, many=True, context={'request': request})
    return Response({
        "topic_title": topic.title,
        "sentences": serializer.data
    })

# API 3: Chi tiết một câu và gợi ý câu tiếp theo
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_practice_detail(request, sentence_id):
    sentence = get_object_or_404(SpeakingSentence, id=sentence_id)
    next_sentence = SpeakingSentence.objects.filter(
        topic=sentence.topic, id__gt=sentence.id
    ).first()
    
    return Response({
        "current_sentence": SpeakingSentenceSerializer(sentence, context={'request': request}).data,
        "next_sentence_id": next_sentence.id if next_sentence else None
    })

# API 4: Xử lý chấm điểm ghi âm (Đã sửa lỗi SuspiciousFileOperation)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_submit_pronunciation(request):
    sentence_id = request.data.get('sentence_id')
    uploaded_audio = request.FILES.get('audio_data') # Đổi tên biến cho rõ ràng
    
    if not sentence_id or not uploaded_audio:
        return Response({"error": "Thiếu dữ liệu"}, status=status.HTTP_400_BAD_REQUEST)
        
    sentence = get_object_or_404(SpeakingSentence, id=sentence_id)

    # 1. Tạo tên file mới để tránh lỗi đường dẫn temp
    file_name = f"user_{request.user.id}_{int(time.time())}.wav"
    
    # 2. Đọc nội dung file vào bộ nhớ
    audio_content = ContentFile(uploaded_audio.read())

    # 3. Tạo Log (Chưa có file)
    log = PronunciationLog.objects.create(
        user=request.user,
        sentence=sentence,
        audio_file=None 
    )

    # 4. Lưu file an toàn vào thư mục media
    log.audio_file.save(file_name, audio_content, save=True)

    # 5. Gọi Azure để chấm điểm (Dùng đường dẫn thực trong media)
    try:
        result = AzureSpeechService.assess_pronunciation(log.audio_file.path, sentence.text)

        if result['success']:
            log.overall_score = result['overall_score']
            log.accuracy_score = result['accuracy_score']
            log.fluency_score = result['fluency_score']
            log.completeness_score = result['completeness_score']
            log.api_response = result['full_response']
            log.save()
            
            return Response(PronunciationLogSerializer(log).data, status=status.HTTP_201_CREATED)
        
        return Response({"error": "Azure API Error: " + result.get('message', '')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API 5: Lưu/Bỏ lưu Topic
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_toggle_save_topic(request, topic_id):
    topic = get_object_or_404(SpeakingTopic, id=topic_id)
    user = request.user
    
    if user in topic.users_who_saved.all():
        topic.users_who_saved.remove(user)
        saved = False
    else:
        topic.users_who_saved.add(user)
        saved = True
        
    return Response({"status": "success", "saved": saved})

# API 6: Danh sách Topic đã lưu
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_saved_topics(request):
    topics = request.user.saved_topics.all().order_by('-created_at')
    serializer = SpeakingTopicSerializer(topics, many=True, context={'request': request})
    return Response(serializer.data)