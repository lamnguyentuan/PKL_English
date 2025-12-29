from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from study.models import Topic, Vocabulary, Flashcard, StudySession, StudyLog, NotebookEntry
from .serializers import (
    TopicSerializer, VocabularySerializer,
    FlashcardSerializer, StudySessionSerializer, StudyLogSerializer, NotebookEntrySerializer
)


# =========================
# 1) PUBLIC TOPICS (Topic hệ thống)
# =========================
class PublicTopicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Topic hệ thống/public: owner=None + is_public=True
        return Topic.objects.filter(is_public=True, owner__isnull=True).order_by("-id")


class PublicVocabularyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VocabularySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Vocabulary.objects.select_related("topic").filter(
            topic__is_public=True,
            topic__owner__isnull=True
        ).order_by("id")

        topic_id = self.request.query_params.get("topic")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        return qs


# =========================
# 2) MY TOPICS (Topic riêng của user)
# =========================
class MyTopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # để upload image nếu có

    def get_queryset(self):
        return Topic.objects.filter(owner=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        # Topic user tạo mặc định private
        serializer.save(owner=self.request.user, is_public=False)

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated])
    def vocabularies(self, request, pk=None):
        """
        GET  /api/v1/study/my-topics/{id}/vocabularies/  -> list vocab của topic riêng
        POST /api/v1/study/my-topics/{id}/vocabularies/  -> tạo vocab trong topic riêng
        """
        topic = self.get_object()  # đảm bảo topic thuộc user (do get_queryset)

        if request.method == "GET":
            qs = Vocabulary.objects.filter(topic=topic).order_by("id")
            ser = VocabularySerializer(qs, many=True, context={"request": request})
            return Response(ser.data)

        ser = VocabularySerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        ser.save(topic=topic)
        return Response(ser.data, status=201)


class MyVocabularyViewSet(viewsets.ModelViewSet):
    """
    CRUD vocab riêng: chỉ cho phép thao tác với vocab nằm trong topic của user.
    Endpoint này giúp bạn PATCH/DELETE vocab riêng dễ hơn (không cần nested).
    """
    serializer_class = VocabularySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # để upload audio

    def get_queryset(self):
        return Vocabulary.objects.select_related("topic").filter(
            topic__owner=self.request.user
        ).order_by("-id")


# =========================
# 3) USER DATA (Flashcard / Session / Log / Notebook)
# =========================
class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.select_related("vocabulary").filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudySessionViewSet(viewsets.ModelViewSet):
    serializer_class = StudySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user).order_by("-start_time")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudyLogViewSet(viewsets.ModelViewSet):
    serializer_class = StudyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudyLog.objects.select_related("vocabulary").filter(user=self.request.user).order_by("-answered_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotebookEntryViewSet(viewsets.ModelViewSet):
    serializer_class = NotebookEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotebookEntry.objects.select_related("vocabulary").filter(user=self.request.user).order_by("-added_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
