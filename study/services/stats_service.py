"""
Service xử lý logic Thống kê (Statistics)
- Thống kê tổng quan
- Thống kê chi tiết
- Log học tập
"""
from django.db import connection
from datetime import date, timedelta
from .utils import dictfetchall


class StatsService:

    # --- 1. THỐNG KÊ TỔNG QUAN ---
    @staticmethod
    def get_stats(user):
        with connection.cursor() as cursor:
            # Đếm xem mỗi level có bao nhiêu thẻ
            cursor.execute("""
                SELECT mastery_level, COUNT(id) as count
                FROM study_flashcard
                WHERE user_id = %s
                GROUP BY mastery_level
            """, [user.id])
            
            rows = cursor.fetchall()  # Trả về dạng [(0, 5), (1, 2)...]

        # Xử lý kết quả cho Frontend
        result = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_learned = 0
        
        for row in rows:
            level = row[0]
            count = row[1]
            result[level] = count
            if level > 0:
                total_learned += count
                
        return {
            'level_counts': result,
            'total_learned': total_learned
        }

    # --- 2. LOG HỌC TẬP ---
    @staticmethod
    def log_answer(user, vocabulary_id, is_correct):
        """Lưu log mỗi lần trả lời"""
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO study_studylog (user_id, vocabulary_id, is_correct, answered_at)
                VALUES (%s, %s, %s, NOW())
            """, [user.id, vocabulary_id, is_correct])

    # --- 3. THỐNG KÊ CHI TIẾT ---
    @staticmethod
    def get_detailed_stats(user):
        """Lấy thống kê chi tiết"""
        with connection.cursor() as cursor:
            stats = {}
            
            # 1. Tổng quan
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_answers,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
                FROM study_studylog
                WHERE user_id = %s
            """, [user.id])
            row = cursor.fetchone()
            stats['total_answers'] = row[0] or 0
            stats['correct_answers'] = row[1] or 0
            stats['accuracy'] = int((stats['correct_answers'] / stats['total_answers']) * 100) if stats['total_answers'] > 0 else 0
            
            # 2. Thống kê 7 ngày gần nhất
            cursor.execute("""
                SELECT 
                    DATE(answered_at) as study_date,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM study_studylog
                WHERE user_id = %s 
                AND answered_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(answered_at)
                ORDER BY study_date ASC
            """, [user.id])
            stats['daily_stats'] = dictfetchall(cursor)
            
            # 3. Từ hay sai nhất (top 5)
            cursor.execute("""
                SELECT 
                    v.word,
                    v.meaning_sentence,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN sl.is_correct = 0 THEN 1 ELSE 0 END) as wrong_count
                FROM study_studylog sl
                JOIN study_vocabulary v ON sl.vocabulary_id = v.id
                WHERE sl.user_id = %s
                GROUP BY sl.vocabulary_id, v.word, v.meaning_sentence
                HAVING wrong_count > 0
                ORDER BY wrong_count DESC
                LIMIT 5
            """, [user.id])
            stats['most_wrong'] = dictfetchall(cursor)
            
            # 4. Từ đã thuộc (level 5)
            cursor.execute("""
                SELECT COUNT(*) FROM study_flashcard
                WHERE user_id = %s AND mastery_level = 5
            """, [user.id])
            stats['mastered_count'] = cursor.fetchone()[0]
            
            # 5. Tổng số từ đang học
            cursor.execute("""
                SELECT COUNT(*) FROM study_flashcard
                WHERE user_id = %s
            """, [user.id])
            stats['total_words'] = cursor.fetchone()[0]
            
            # 6. Streak (số ngày học liên tục)
            cursor.execute("""
                SELECT DISTINCT DATE(answered_at) as study_date
                FROM study_studylog
                WHERE user_id = %s
                ORDER BY study_date DESC
            """, [user.id])
            dates = [row[0] for row in cursor.fetchall()]
            
            streak = 0
            today = date.today()
            
            for i, d in enumerate(dates):
                expected_date = today - timedelta(days=i)
                if d == expected_date:
                    streak += 1
                else:
                    break
            
            stats['streak'] = streak
            
            return stats
