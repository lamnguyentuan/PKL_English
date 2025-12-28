from datetime import date, timedelta
from django.db.models import Count, Sum, Case, When, IntegerField, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from study.models import Flashcard, StudyLog

class StatsService:
    """
    Service xử lý logic thống kê dùng Django ORM
    """

    # --- 1. THỐNG KÊ TỔNG QUAN (Level Counts) ---
    @staticmethod
    def get_stats(user):
        # Lấy số lượng thẻ theo từng level
        # Output: [{'mastery_level': 0, 'count': 5}, {'mastery_level': 1, 'count': 2}]
        level_counts = Flashcard.objects.filter(user=user)\
            .values('mastery_level')\
            .annotate(count=Count('id'))

        # Chuẩn hóa kết quả trả về (đảm bảo đủ level 0-5)
        result = {i: 0 for i in range(6)}
        total_learned = 0
        
        for item in level_counts:
            level = item['mastery_level']
            count = item['count']
            if level in result:
                result[level] = count
            
            if level > 0:
                total_learned += count

        return {
            'level_counts': result,
            'total_learned': total_learned
        }

    # --- 2. LOG HỌC TẬP (Đã tích hợp vào StudyService, hàm này có thể bỏ hoặc giữ làm wrapper) ---
    @staticmethod
    def log_answer(user, vocabulary, is_correct):
        StudyLog.objects.create(
            user=user,
            vocabulary=vocabulary,
            is_correct=is_correct,
            answered_at=timezone.now()
        )

    # --- 3. THỐNG KÊ CHI TIẾT ---
    @staticmethod
    def get_detailed_stats(user):
        stats = {}
        
        # A. TỔNG QUAN
        # aggregate trả về dict: {'total': 100, 'correct': 80}
        overview = StudyLog.objects.filter(user=user).aggregate(
            total_answers=Count('id'),
            correct_answers=Count(Case(When(is_correct=True, then=1)))
        )
        
        total = overview['total_answers'] or 0
        correct = overview['correct_answers'] or 0
        stats['total_answers'] = total
        stats['correct_answers'] = correct
        stats['accuracy'] = int((correct / total) * 100) if total > 0 else 0

        # B. THỐNG KÊ 7 NGÀY GẦN NHẤT
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        
        daily_stats_query = StudyLog.objects.filter(
            user=user, 
            answered_at__date__gte=seven_days_ago
        ).annotate(
            study_date=TruncDate('answered_at')
        ).values('study_date').annotate(
            total=Count('id'),
            correct=Count(Case(When(is_correct=True, then=1)))
        ).order_by('study_date')

        # Convert queryset to list
        stats['daily_stats'] = list(daily_stats_query)

        # C. TỪ HAY SAI NHẤT (TOP 5)
        # Lọc những log trả lời sai
        wrong_logs = StudyLog.objects.filter(user=user, is_correct=False)
        
        # Group by vocabulary, đếm số lần sai
        most_wrong = wrong_logs.values(
            'vocabulary__word', 
            'vocabulary__meaning_sentence'
        ).annotate(
            wrong_count=Count('id')
        ).order_by('-wrong_count')[:5]

        # Format lại kết quả cho giống code cũ
        stats['most_wrong'] = [
            {
                'word': item['vocabulary__word'],
                'meaning_sentence': item['vocabulary__meaning_sentence'],
                'wrong_count': item['wrong_count']
                # Lưu ý: 'total_attempts' khó tính gộp bằng ORM đơn giản trong 1 query này, 
                # nhưng thường chỉ cần biết sai bao nhiêu lần là đủ để ôn tập.
            } 
            for item in most_wrong
        ]

        # D. TỪ ĐÃ THUỘC (Level = 5) & TỔNG SỐ TỪ
        flashcard_stats = Flashcard.objects.filter(user=user).aggregate(
            mastered=Count(Case(When(mastery_level=5, then=1))),
            total=Count('id')
        )
        stats['mastered_count'] = flashcard_stats['mastered']
        stats['total_words'] = flashcard_stats['total']

        # E. TÍNH STREAK (Chuỗi ngày liên tục)
        # Lấy danh sách ngày distinct đã học, sắp xếp giảm dần
        study_dates = StudyLog.objects.filter(user=user)\
            .annotate(date_only=TruncDate('answered_at'))\
            .values_list('date_only', flat=True)\
            .distinct()\
            .order_by('-date_only')

        streak = 0
        today = timezone.now().date()
        
        # Logic: Check ngày hôm nay hoặc hôm qua có học không để bắt đầu đếm
        # (Nếu hôm nay chưa học, nhưng hôm qua học thì chuỗi vẫn chưa đứt)
        
        if not study_dates:
            stats['streak'] = 0
            return stats

        last_study_date = study_dates[0]
        
        # Nếu ngày học cuối cùng cách hôm nay quá 1 ngày -> Mất chuỗi
        if (today - last_study_date).days > 1:
            stats['streak'] = 0
            return stats
            
        # Bắt đầu đếm ngược
        check_date = last_study_date
        for d in study_dates:
            if d == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        stats['streak'] = streak
        return stats