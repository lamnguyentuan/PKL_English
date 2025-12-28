from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# --- 1. TRANG CHỦ (Landing Page) ---
# URL: http://127.0.0.1:8000/
def home_page(request):
    return render(request, 'index.html')

# --- 2. STUDY APP (Học Từ Vựng) ---

# Trang danh sách chủ đề (URL: /study/)
@login_required
def study_topic_list(request):
    return render(request, 'study/topic_list.html')

# Trang học Flashcard (URL: /study/flashcards/<id>/)
@login_required
def study_flashcards(request, topic_id):
    # Truyền topic_id xuống để Javascript biết gọi API nào
    return render(request, 'study/flashcard_view.html', {'topic_id': topic_id})