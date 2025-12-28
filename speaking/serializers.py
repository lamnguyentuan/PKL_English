from rest_framework import serializers
from .models import SpeakingTopic, SpeakingSentence, PronunciationLog


class SpeakingSentenceSerializer(serializers.ModelSerializer):
    """Serializer for SpeakingSentence"""
    class Meta:
        model = SpeakingSentence
        fields = ['id', 'topic', 'text', 'translation']


class SpeakingTopicSerializer(serializers.ModelSerializer):
    """Serializer for SpeakingTopic"""
    sentence_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SpeakingTopic
        fields = ['id', 'title', 'description', 'image', 'sentence_count', 'created_at']
    
    def get_sentence_count(self, obj):
        return obj.sentences.count()


class SpeakingTopicDetailSerializer(SpeakingTopicSerializer):
    """Serializer for SpeakingTopic with sentences"""
    sentences = SpeakingSentenceSerializer(many=True, read_only=True)
    
    class Meta(SpeakingTopicSerializer.Meta):
        fields = SpeakingTopicSerializer.Meta.fields + ['sentences']


class PronunciationLogSerializer(serializers.ModelSerializer):
    """Serializer for PronunciationLog"""
    sentence = SpeakingSentenceSerializer(read_only=True)
    
    class Meta:
        model = PronunciationLog
        fields = ['id', 'sentence', 'audio_file', 'overall_score', 
                  'accuracy_score', 'fluency_score', 'completeness_score', 
                  'api_response', 'created_at']


class SubmitPronunciationSerializer(serializers.Serializer):
    """Serializer for submitting pronunciation"""
    sentence_id = serializers.IntegerField()
    audio_data = serializers.FileField()


class PronunciationResultSerializer(serializers.Serializer):
    """Response serializer for pronunciation assessment"""
    success = serializers.BooleanField()
    overall_score = serializers.FloatField()
    accuracy_score = serializers.FloatField()
    fluency_score = serializers.FloatField()
    completeness_score = serializers.FloatField()
    full_response = serializers.DictField()
