from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from study.models import Vocabulary  # Import từ app study

class PronunciationLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    
    # File ghi âm của user
    audio_file = models.FileField(upload_to="user_practice/")
    
    # Kết quả chấm điểm (Lưu JSON để linh hoạt với mọi API)
    overall_score = models.FloatField(default=0.0)
    api_response = models.JSONField(default=dict, blank=True)  # Lưu toàn bộ phản hồi từ AI
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.vocabulary.word} - {self.overall_score}"