from rest_framework import serializers
from .models import Topic, Vocabulary, Flashcard, NotebookEntry, StudyLog


class VocabularySerializer(serializers.ModelSerializer):
    """Serializer for Vocabulary"""
    class Meta:
        model = Vocabulary
        fields = ['id', 'topic', 'word', 'phonetic', 'definition', 
                  'meaning_sentence', 'example_sentence', 'audio', 'created_at']
        read_only_fields = ['id', 'created_at']


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic"""
    vocabulary_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = ['id', 'title', 'description', 'image', 'vocabulary_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_vocabulary_count(self, obj):
        return obj.vocabularies.count()


class TopicDetailSerializer(TopicSerializer):
    """Serializer for Topic with vocabularies"""
    vocabularies = VocabularySerializer(many=True, read_only=True)
    
    class Meta(TopicSerializer.Meta):
        fields = TopicSerializer.Meta.fields + ['vocabularies']


class FlashcardSerializer(serializers.ModelSerializer):
    """Serializer for Flashcard"""
    vocabulary = VocabularySerializer(read_only=True)
    vocabulary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Flashcard
        fields = ['id', 'vocabulary', 'vocabulary_id', 'mastery_level', 'last_reviewed', 'created_at']
        read_only_fields = ['id', 'mastery_level', 'last_reviewed', 'created_at']


class NotebookEntrySerializer(serializers.ModelSerializer):
    """Serializer for NotebookEntry"""
    vocabulary = VocabularySerializer(read_only=True)
    vocabulary_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = NotebookEntry
        fields = ['id', 'vocabulary', 'vocabulary_id', 'note', 'added_at']
        read_only_fields = ['id', 'added_at']


class StudyLogSerializer(serializers.ModelSerializer):
    """Serializer for StudyLog"""
    vocabulary = VocabularySerializer(read_only=True)
    
    class Meta:
        model = StudyLog
        fields = ['id', 'vocabulary', 'is_correct', 'answered_at']
        read_only_fields = ['id', 'answered_at']


class SubmitAnswerSerializer(serializers.Serializer):
    """Serializer for submitting answer"""
    card_id = serializers.IntegerField()
    user_answer = serializers.CharField()


class SubmitAnswerResponseSerializer(serializers.Serializer):
    """Response serializer for answer submission"""
    is_correct = serializers.BooleanField()
    new_level = serializers.IntegerField()
    word = serializers.CharField()
    phonetic = serializers.CharField()
    meaning = serializers.CharField()
    audio = serializers.CharField(allow_blank=True)


class StudyStatsSerializer(serializers.Serializer):
    """Serializer for study statistics"""
    total_answers = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    accuracy = serializers.IntegerField()
    mastered_count = serializers.IntegerField()
    total_words = serializers.IntegerField()
    streak = serializers.IntegerField()
