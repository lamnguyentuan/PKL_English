from django.contrib import admin
from .models import Topic, Vocabulary, Flashcard, StudySession, StudyLog, NotebookEntry

# --- Inline để thêm Vocabulary ngay trong trang Topic ---
class VocabularyInline(admin.TabularInline):
    model = Vocabulary
    extra = 1  # Số dòng trống để thêm mới
    fields = ['word', 'phonetic', 'definition', 'example_sentence', 'meaning_sentence', 'audio']


# --- Admin cho Topic ---
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'vocabulary_count']
    search_fields = ['title', 'description']
    inlines = [VocabularyInline]
    
    def vocabulary_count(self, obj):
        return obj.vocabularies.count()
    vocabulary_count.short_description = 'Số từ vựng'


# --- Admin cho Vocabulary ---
@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ['word', 'topic', 'phonetic', 'definition']
    list_filter = ['topic']
    search_fields = ['word', 'definition']


# --- Admin cho Flashcard ---
@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['user', 'vocabulary', 'mastery_level', 'last_reviewed']
    list_filter = ['user', 'mastery_level']
    search_fields = ['user__username', 'vocabulary__word']


# --- Admin cho StudySession ---
@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'start_time', 'end_time', 'score']
    list_filter = ['user', 'topic']


# --- Admin cho StudyLog ---
@admin.register(StudyLog)
class StudyLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'vocabulary', 'is_correct', 'answered_at']
    list_filter = ['user', 'is_correct']


# --- Admin cho NotebookEntry ---
@admin.register(NotebookEntry)
class NotebookEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'vocabulary', 'added_at']
    list_filter = ['user']
    search_fields = ['vocabulary__word', 'note']
