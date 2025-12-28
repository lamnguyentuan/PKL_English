from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import random
import time

from .models import SpeakingTopic, SpeakingSentence, PronunciationLog
from .serializers import (
    SpeakingTopicSerializer, 
    SpeakingTopicDetailSerializer,
    SubmitPronunciationSerializer,
    PronunciationResultSerializer
)

# Thử import service cũ của bạn. 
# Nếu chưa refactor thư mục services, bạn có thể tạm comment dòng này và dùng Mock AI bên dưới.
try:
    from .services.services import AzureSpeechService
except ImportError:
    AzureSpeechService = None

# --- 1. API: DANH SÁCH & CHI TIẾT CHỦ ĐỀ ---
class SpeakingTopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - GET /api/speaking/topics/ -> Lấy danh sách (Giống topic_list cũ)
    - GET /api/speaking/topics/{id}/ -> Lấy chi tiết kèm câu hỏi (Giống sentence_list cũ)
    """
    queryset = SpeakingTopic.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SpeakingTopicDetailSerializer
        return SpeakingTopicSerializer


# --- 2. API: NỘP BÀI GHI ÂM (Thay thế submit_pronunciation) ---
class SubmitPronunciationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] # Để nhận file âm thanh upload

    def post(self, request, *args, **kwargs):
        serializer = SubmitPronunciationSerializer(data=request.data)
        
        if serializer.is_valid():
            sentence_id = serializer.validated_data['sentence_id']
            audio_file = serializer.validated_data['audio_data']
            
            sentence = get_object_or_404(SpeakingSentence, id=sentence_id)

            # BƯỚC 1: Tạo log tạm để lưu file vật lý xuống ổ cứng
            # (Azure cần đường dẫn file thực tế)
            log = PronunciationLog.objects.create(
                user=request.user,
                sentence=sentence,
                audio_file=audio_file,
                overall_score=0 # Điểm tạm
            )

            # BƯỚC 2: Gọi Azure Service (Logic cũ của bạn)
            if AzureSpeechService:
                try:
                    # Gọi hàm assess_pronunciation từ code cũ của bạn
                    result = AzureSpeechService.assess_pronunciation(log.audio_file.path, sentence.text)
                except Exception as e:
                    # Nếu lỗi Azure, trả về lỗi server
                    print(f"Azure Error: {e}")
                    return Response({"error": "Lỗi kết nối Azure AI"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Nếu không có AzureService (lúc test), dùng Mock AI
                result = self.mock_ai_scoring(sentence.text)

            # BƯỚC 3: Cập nhật kết quả vào DB
            if result.get('success', False) or 'overall_score' in result:
                # Lưu ý: Cần map đúng key trả về từ Service của bạn
                log.overall_score = result.get('overall_score', 0)
                log.accuracy_score = result.get('accuracy_score', 0)
                log.fluency_score = result.get('fluency_score', 0)
                log.completeness_score = result.get('completeness_score', 0)
                log.api_response = result.get('full_response', result)
                log.save()

                # BƯỚC 4: Trả kết quả JSON về cho Frontend
                response_data = {
                    'success': True,
                    'overall_score': log.overall_score,
                    'accuracy_score': log.accuracy_score,
                    'fluency_score': log.fluency_score,
                    'completeness_score': log.completeness_score,
                    'full_response': log.api_response
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": "Không nhận diện được âm thanh"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def mock_ai_scoring(self, text):
        """Hàm giả lập nếu chưa cấu hình Azure"""
        time.sleep(1)
        overall = round(random.uniform(60, 100), 1)
        return {
            "success": True,
            "overall_score": overall,
            "accuracy_score": round(random.uniform(overall - 5, 100), 1),
            "fluency_score": round(random.uniform(60, 95), 1),
            "completeness_score": 100.0,
            "full_response": {"mock": "Dữ liệu giả lập (Chưa import AzureSpeechService)"}
        }