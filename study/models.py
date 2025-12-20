from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings  # Để gọi User đúng chuẩn
from django.utils import timezone

# --- 1. DỮ LIỆU TĨNH (Nội dung bài học) ---
class Topic(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tên chủ đề")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to='topic_images/', null=True, blank=True)
    
    def __str__(self):
        return self.title

class Vocabulary(models.Model):
    topic = models.ForeignKey(Topic, related_name='vocabularies', on_delete=models.CASCADE)
    word = models.CharField(max_length=100, verbose_name="Từ vựng")
    phonetic = models.CharField(max_length=100, blank=True, verbose_name="Phiên âm")
    definition = models.TextField(verbose_name="Định nghĩa")
    example_sentence = models.TextField(blank=True, verbose_name="Câu ví dụ")
    meaning_sentence = models.TextField(blank=True, verbose_name="Nghĩa câu ví dụ")
    audio = models.FileField(upload_to="vocab_audio/", blank=True, null=True, verbose_name="Audio mẫu")
    
    def __str__(self):
        return self.word

# --- 2. DỮ LIỆU ĐỘNG (Tiến độ học tập của từng User) ---
class Flashcard(models.Model):
  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    

    mastery_level = models.IntegerField(default=0)    
    last_reviewed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        # Đảm bảo mỗi user chỉ có 1 thẻ flashcard cho 1 từ vựng
        unique_together = ('user', 'vocabulary') 

    def __str__(self):
        return f"{self.user.username} - {self.vocabulary.word} - (Lv{self.mastery_level})"

# --- 3. LOG & SỔ TAY ---
class StudySession(models.Model):
    """Lịch sử mỗi lần ngồi vào học"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0) # Điểm số bài test cuối phiên

class NotebookEntry(models.Model):
    """Sổ tay từ khó"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    note = models.TextField(blank=True, verbose_name="Ghi chú cá nhân")
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'vocabulary')