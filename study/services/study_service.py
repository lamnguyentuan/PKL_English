"""

Các service  được tách ra thành:
    - flashcard_service.py: FlashcardService
    - notebook_service.py: NotebookService  
    - stats_service.py: StatsService
    - utils.py: Các hàm tiện ích

"""

# Re-export để code cũ vẫn hoạt động
from . import StudyService

__all__ = ['StudyService']
