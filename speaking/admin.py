from django.contrib import admin
from .models import SpeakingTopic, SpeakingSentence

# Cấu hình hiển thị các câu nằm ngay trong trang của Topic
class SpeakingSentenceInline(admin.TabularInline):
    model = SpeakingSentence
    extra = 3  # Hiển thị sẵn 3 ô trống để nhập nhanh
    fields = ('text', 'translation')

@admin.register(SpeakingTopic)
class SpeakingTopicAdmin(admin.ModelAdmin):
    # Các cột hiển thị ở danh sách bên ngoài
    list_display = ('id', 'title', 'created_at', 'get_sentence_count')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)
    
    # Tích hợp phần thêm câu vào chung một trang
    inlines = [SpeakingSentenceInline]

    # Hàm đếm số câu trong mỗi Topic
    def get_sentence_count(self, obj):
        return obj.sentences.count()
    get_sentence_count.short_description = "Số lượng câu"

@admin.register(SpeakingSentence)
class SpeakingSentenceAdmin(admin.ModelAdmin):
    list_display = ('text', 'topic', 'translation')
    list_filter = ('topic',)
    search_fields = ('text', 'translation')