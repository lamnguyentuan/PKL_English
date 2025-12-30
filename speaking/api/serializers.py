from rest_framework import serializers
from ..models import SpeakingTopic, SpeakingSentence, PronunciationLog

# 1. Serializer cho Nhật ký phát âm (PronunciationLog)
class PronunciationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PronunciationLog
        fields = [
            'id', 'user', 'sentence', 'audio_file', 'overall_score', 
            'accuracy_score', 'fluency_score', 'completeness_score', 
            'api_response', 'created_at'
        ]
        read_only_fields = ['user', 'created_at'] # Các trường này server tự điền

# 2. Serializer cho Câu mẫu (SpeakingSentence)
class SpeakingSentenceSerializer(serializers.ModelSerializer):
    # Hiển thị lịch sử luyện tập gần nhất của user cho câu này (Tùy chọn)
    last_log_score = serializers.SerializerMethodField()

    class Meta:
        model = SpeakingSentence
        fields = ['id', 'topic', 'text', 'translation', 'last_log_score']

    def get_last_log_score(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            log = PronunciationLog.objects.filter(user=request.user, sentence=obj).first()
            return log.overall_score if log else None
        return None

# 3. Serializer cho Chủ đề (SpeakingTopic)
class SpeakingTopicSerializer(serializers.ModelSerializer):
    # Lấy luôn danh sách các câu thuộc chủ đề này
    sentences = SpeakingSentenceSerializer(many=True, read_only=True)
    
    # Kiểm tra xem User hiện tại đã lưu chủ đề này chưa
    is_saved = serializers.SerializerMethodField()
    
    # Đếm số lượng câu mẫu trong chủ đề
    sentence_count = serializers.IntegerField(source='sentences.count', read_only=True)

    class Meta:
        model = SpeakingTopic
        fields = ['id', 'title', 'description', 'image', 'created_at', 'sentences', 'is_saved', 'sentence_count']

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.users_who_saved.filter(id=request.user.id).exists()
        return False