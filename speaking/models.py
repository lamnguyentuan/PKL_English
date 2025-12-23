from django.db import models
from django.conf import settings

class SpeakingTopic(models.Model):
    # Tất cả các dòng dưới đây phải thụt lề vào
    title = models.CharField(max_length=200, verbose_name="Tiêu đề chủ đề")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to='speaking_topics/', null=True, blank=True, verbose_name="Hình ảnh minh họa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    def __str__(self):
        return self.title

class SpeakingSentence(models.Model):
    # Các dòng này cũng phải thụt lề
    topic = models.ForeignKey(SpeakingTopic, on_delete=models.CASCADE, related_name='sentences', verbose_name="Chủ đề")
    text = models.CharField(max_length=500, verbose_name="Câu mẫu (Tiếng Anh)")
    translation = models.CharField(max_length=500, blank=True, verbose_name="Dịch nghĩa (Tiếng Việt)")
    
    def __str__(self):
        return f"{self.topic.title} - {self.text[:30]}"

class PronunciationLog(models.Model):
    # Các dòng này cũng phải thụt lề
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Người dùng")
    sentence = models.ForeignKey(SpeakingSentence, on_delete=models.CASCADE, related_name='logs', null=True, verbose_name="Câu đã luyện")
    audio_file = models.FileField(upload_to="speaking_recordings/", verbose_name="File ghi âm")
    overall_score = models.FloatField(default=0.0, verbose_name="Điểm tổng quan")
    accuracy_score = models.FloatField(default=0.0, verbose_name="Độ chính xác")
    fluency_score = models.FloatField(default=0.0, verbose_name="Độ lưu loát")
    completeness_score = models.FloatField(default=0.0, verbose_name="Độ hoàn thành")
    api_response = models.JSONField(default=dict, blank=True, verbose_name="Phản hồi từ API")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian luyện tập")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Nhật ký phát âm"
        verbose_name_plural = "Danh sách nhật ký phát âm"

    def __str__(self):
        return f"{self.user.username} - {self.overall_score}"