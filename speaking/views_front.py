from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# 1. Trang danh sách chủ đề (Frontend)
def speaking_topic_list(request):
    return render(request, 'speaking/topic_list.html')

# 2. Trang luyện tập (Frontend)
@login_required
def speaking_practice(request, topic_id):
    # Truyền topic_id xuống để Javascript biết đang học bài nào
    return render(request, 'speaking/practice.html', {'topic_id': topic_id})