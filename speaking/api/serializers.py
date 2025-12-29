from rest_framework import serializers
from speaking.models import SpeakingTopic, SpeakingSentence, PronunciationLog


class SpeakingSentenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingSentence
        fields = ["id", "topic", "text", "translation"]


class SpeakingTopicSerializer(serializers.ModelSerializer):
    sentences = SpeakingSentenceSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SpeakingTopic
        fields = ["id", "title", "description", "image", "image_url", "created_at", "sentences"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class PronunciationLogSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    # thêm field tiện hiển thị
    sentence_text = serializers.CharField(source="sentence.text", read_only=True)
    topic_id = serializers.IntegerField(source="sentence.topic_id", read_only=True)
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = PronunciationLog
        fields = [
            "id",
            "user",
            "sentence",
            "sentence_text",
            "topic_id",
            "audio_file",
            "audio_url",
            "overall_score",
            "accuracy_score",
            "fluency_score",
            "completeness_score",
            "api_response",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at", "sentence_text", "topic_id", "audio_url"]

    def get_audio_url(self, obj):
        request = self.context.get("request")
        if not obj.audio_file:
            return None
        url = obj.audio_file.url if hasattr(obj.audio_file, "url") else None
        if not url:
            return None
        return request.build_absolute_uri(url) if request else url
