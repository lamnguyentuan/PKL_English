"""
Study Services Package

Export tất cả service để dễ import.
Giữ tương thích ngược với code cũ qua class StudyService.
"""
from .utils import dictfetchall
from .flashcard_service import FlashcardService
from .notebook_service import NotebookService
from .stats_service import StatsService


# Class tổng hợp - giữ tương thích ngược với code cũ
# Các views.py cũ dùng StudyService.xxx() vẫn hoạt động
class StudyService(FlashcardService, NotebookService, StatsService):
    """
    Class tổng hợp tất cả service.
    Kế thừa từ: FlashcardService, NotebookService, StatsService
    
    Sử dụng:
        from .services import StudyService
        # hoặc
        from .services.study_service import StudyService  (tương thích ngược)
    """
    pass


__all__ = [
    'StudyService',
    'FlashcardService',
    'NotebookService', 
    'StatsService',
    'dictfetchall',
]
