from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

# Import Models
from .models import Topic, NotebookEntry

# Import Serializers 
# (Đảm bảo file serializers.py của bạn đã có các class này)
from .serializers import (
    TopicSerializer, 
    TopicDetailSerializer, 
    NotebookEntrySerializer
)

# Import Services (Ngắn gọn nhờ file __init__.py ở trên)
from .services import NotebookService, StudyService, StatsService


# ==========================================
# NHÓM 1: QUẢN LÝ CHỦ ĐỀ (TOPIC)
# ==========================================
class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API:
    - GET /topics/ : Danh sách chủ đề
    - GET /topics/{id}/ : Chi tiết chủ đề (kèm từ vựng)
    - POST /topics/{id}/reset_progress/ : Reset học lại từ đầu
    """
    queryset = Topic.objects.all().order_by('id')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Dùng serializer chi tiết (có list từ vựng) khi xem 1 topic
        if self.action == 'retrieve':
            return TopicDetailSerializer
        return TopicSerializer

    @action(detail=True, methods=['post'])
    def reset_progress(self, request, pk=None):
        """Reset tiến độ học của topic này"""
        StudyService.reset_topic_progress(request.user, pk)
        return Response({'message': 'Đã reset tiến độ học về 0'}, status=status.HTTP_200_OK)


# ==========================================
# NHÓM 2: SỔ TAY TỪ VỰNG (NOTEBOOK CRUD)
# ==========================================
class NotebookViewSet(viewsets.ModelViewSet):
    """
    API CRUD Sổ tay:
    - GET /notebook/ : Xem danh sách
    - POST /notebook/ : Thêm từ vào sổ tay
    - PATCH /notebook/{id}/ : Sửa ghi chú
    - DELETE /notebook/{id}/ : Xóa khỏi sổ tay
    """
    serializer_class = NotebookEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotebookEntry.objects.filter(user=self.request.user).order_by('-added_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==========================================
# NHÓM 3: LOGIC ÔN TẬP SỔ TAY (REVIEW)
# ==========================================
class NotebookReviewView(APIView):
    """
    API lấy câu hỏi ôn tập từ sổ tay.
    URL: GET /api/notebook/review/?excluded_ids=1,2,3
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Lấy danh sách ID đã học trong phiên để loại trừ
        excluded_string = request.query_params.get('excluded_ids', '')
        excluded_ids = [int(x) for x in excluded_string.split(',') if x.isdigit()]

        question = NotebookService.get_notebook_review_question(request.user, excluded_ids)
        
        if question:
            return Response(question)
        
        return Response({"message": "Hoàn thành ôn tập", "finished": True}, status=status.HTTP_200_OK)

class NotebookSubmitAnswerView(APIView):
    """
    API kiểm tra đáp án ôn tập sổ tay.
    URL: POST /api/notebook/submit/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        vocab_id = request.data.get('vocabulary_id')
        question_type = request.data.get('type', 'listening') # 'listening' hoặc 'fill_blank'
        
        if question_type == 'fill_blank':
            user_answer = request.data.get('user_answer', '')
            result = NotebookService.check_fill_blank_review(vocab_id, user_answer)
        else: 
            # Listening: check ID chọn có trùng ID đúng không
            selected_id = request.data.get('selected_id')
            is_correct = str(vocab_id) == str(selected_id)
            result = {'is_correct': is_correct}
            
        return Response(result)


# ==========================================
# NHÓM 4: HỌC TỪ MỚI (FLASHCARD FLOW)
# ==========================================
class StudyCardView(APIView):
    """
    API Lấy thẻ tiếp theo để học (thuật toán Spaced Repetition).
    URL: GET /api/study/card/{topic_id}/?excluded_ids=...
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, topic_id):
        excluded_string = request.query_params.get('excluded_ids', '')
        excluded_ids = [int(x) for x in excluded_string.split(',') if x.isdigit()]

        question_data = StudyService.get_learning_card(request.user, topic_id, excluded_ids)

        if question_data:
            return Response(question_data)
        
        return Response(
            {"message": "Bạn đã hoàn thành bài học hôm nay!", "finished": True}, 
            status=status.HTTP_200_OK
        )

class StudySubmitAnswerView(APIView):
    """
    API Nộp đáp án và chấm điểm.
    URL: POST /api/study/submit/
    Body: { "card_id": 1, "user_answer": "hello" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        card_id = request.data.get('card_id')
        user_answer = request.data.get('user_answer', '')

        if not card_id:
            return Response({"error": "Thiếu card_id"}, status=status.HTTP_400_BAD_REQUEST)

        result = StudyService.check_answer(request.user, card_id, user_answer)
        
        if 'error' in result:
             return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result)


# ==========================================
# NHÓM 5: THỐNG KÊ (STATS)
# ==========================================
class StudyStatsView(APIView):
    """
    API Thống kê chi tiết cho Dashboard.
    URL: GET /api/study/stats/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Gọi StatsService để lấy dữ liệu (đã tính toán bằng ORM)
        stats = StatsService.get_detailed_stats(request.user)
        return Response(stats)