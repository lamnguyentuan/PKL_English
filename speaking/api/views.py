from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from speaking.models import SpeakingTopic, SpeakingSentence, PronunciationLog
from .serializers import (
    SpeakingTopicSerializer,
    SpeakingSentenceSerializer,
    PronunciationLogSerializer,
)


class SpeakingTopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SpeakingTopic.objects.all().order_by("-created_at")
    serializer_class = SpeakingTopicSerializer
    permission_classes = [permissions.AllowAny]


class SpeakingSentenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SpeakingSentence.objects.select_related("topic").all()
    serializer_class = SpeakingSentenceSerializer
    permission_classes = [permissions.AllowAny]

    # optional: filter theo topic ?topic=ID
    def get_queryset(self):
        qs = super().get_queryset()
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        return qs


class PronunciationLogViewSet(viewsets.ModelViewSet):
    serializer_class = PronunciationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # để upload audio_file

    def get_queryset(self):
        return (
            PronunciationLog.objects
            .select_related("sentence", "sentence__topic", "user")
            .filter(user=self.request.user)
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
