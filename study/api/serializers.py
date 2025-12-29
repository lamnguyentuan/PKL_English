from rest_framework import serializers
from study.models import (
    Topic, Vocabulary, Flashcard,
    StudySession, StudyLog, NotebookEntry
)


# -------- TOPIC --------
class TopicSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    # 2 field này phục vụ feature "topic riêng của user"
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    is_public = serializers.BooleanField(required=False)

    class Meta:
        model = Topic
        fields = ["id", "title", "description", "image", "image_url", "owner", "is_public"]
        read_only_fields = ["id", "image_url", "owner"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not getattr(obj, "image", None):
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


# -------- VOCABULARY --------
class VocabularySerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = Vocabulary
        fields = [
            "id", "topic", "topic_title",
            "word", "phonetic", "definition",
            "example_sentence", "meaning_sentence",
            "audio", "audio_url",
        ]
        read_only_fields = ["id", "topic_title", "audio_url"]

    def get_audio_url(self, obj):
        request = self.context.get("request")
        if not getattr(obj, "audio", None):
            return None
        url = obj.audio.url
        return request.build_absolute_uri(url) if request else url


# -------- FLASHCARD / SESSION / LOG / NOTEBOOK --------
class FlashcardSerializer(serializers.ModelSerializer):
    vocabulary_word = serializers.CharField(source="vocabulary.word", read_only=True)
    vocabulary_definition = serializers.CharField(source="vocabulary.definition", read_only=True)

    class Meta:
        model = Flashcard
        fields = [
            "id", "user", "vocabulary",
            "vocabulary_word", "vocabulary_definition",
            "mastery_level", "last_reviewed",
        ]
        read_only_fields = ["id", "user", "vocabulary_word", "vocabulary_definition"]


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = ["id", "user", "topic", "start_time", "end_time", "score"]
        read_only_fields = ["id", "user", "start_time"]


class StudyLogSerializer(serializers.ModelSerializer):
    vocabulary_word = serializers.CharField(source="vocabulary.word", read_only=True)

    class Meta:
        model = StudyLog
        fields = ["id", "user", "vocabulary", "vocabulary_word", "is_correct", "answered_at"]
        read_only_fields = ["id", "user", "answered_at", "vocabulary_word"]


class NotebookEntrySerializer(serializers.ModelSerializer):
    vocabulary_word = serializers.CharField(source="vocabulary.word", read_only=True)

    class Meta:
        model = NotebookEntry
        fields = ["id", "user", "vocabulary", "vocabulary_word", "note", "added_at"]
        read_only_fields = ["id", "user", "added_at", "vocabulary_word"]
