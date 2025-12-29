from rest_framework.routers import DefaultRouter
from .views import SpeakingTopicViewSet, SpeakingSentenceViewSet, PronunciationLogViewSet

router = DefaultRouter()
router.register(r"topics", SpeakingTopicViewSet, basename="speaking-topic")
router.register(r"sentences", SpeakingSentenceViewSet, basename="speaking-sentence")
router.register(r"logs", PronunciationLogViewSet, basename="pronunciation-log")

urlpatterns = router.urls
