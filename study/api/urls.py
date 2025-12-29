from rest_framework.routers import DefaultRouter
from .views import (
    PublicTopicViewSet, PublicVocabularyViewSet,
    MyTopicViewSet, MyVocabularyViewSet,
    FlashcardViewSet, StudySessionViewSet, StudyLogViewSet, NotebookEntryViewSet
)

router = DefaultRouter()

# Public (hệ thống)
router.register(r"topics", PublicTopicViewSet, basename="study-public-topics")
router.register(r"vocabularies", PublicVocabularyViewSet, basename="study-public-vocabularies")

# Private (user tự tạo)
router.register(r"my-topics", MyTopicViewSet, basename="study-my-topics")
router.register(r"my-vocabularies", MyVocabularyViewSet, basename="study-my-vocabularies")

# User data
router.register(r"flashcards", FlashcardViewSet, basename="study-flashcards")
router.register(r"sessions", StudySessionViewSet, basename="study-sessions")
router.register(r"logs", StudyLogViewSet, basename="study-logs")
router.register(r"notebook", NotebookEntryViewSet, basename="study-notebook")

urlpatterns = router.urls
