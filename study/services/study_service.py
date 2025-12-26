import random
import re
from django.db.models import F, Q
from django.utils import timezone
from study.models import Flashcard, Vocabulary, StudyLog, Topic

class StudyService:
    """
    Service xử lý logic học tập chính (Flashcard & Spaced Repetition)
    """

    # --- 1. LẤY THẺ HỌC ---
    @staticmethod
    def get_learning_card(user, topic_id, excluded_card_ids=None):
        if excluded_card_ids is None:
            excluded_card_ids = []

        # BƯỚC A: ĐỒNG BỘ DỮ LIỆU (Sync)
        # Thay vì viết SQL phức tạp, ta dùng logic Python + ORM
        
        # 1. Lấy tất cả ID từ vựng của Topic
        topic_vocab_ids = set(
            Vocabulary.objects.filter(topic_id=topic_id).values_list('id', flat=True)
        )
        
        # 2. Lấy ID từ vựng User đã có thẻ
        existing_vocab_ids = set(
            Flashcard.objects.filter(user=user, vocabulary__topic_id=topic_id)
            .values_list('vocabulary_id', flat=True)
        )
        
        # 3. Tìm từ còn thiếu
        missing_ids = topic_vocab_ids - existing_vocab_ids
        
        # 4. Tạo thẻ mới (Bulk Create để tối ưu tốc độ)
        if missing_ids:
            new_flashcards = [
                Flashcard(user=user, vocabulary_id=vid, mastery_level=0)
                for vid in missing_ids
            ]
            Flashcard.objects.bulk_create(new_flashcards)

        # BƯỚC B: LẤY 1 THẺ ĐỂ HỌC (Queryset)
        # Logic ưu tiên: Chưa học bao giờ (None) -> Học lâu nhất -> Random
        
        queryset = Flashcard.objects.filter(
            user=user, 
            vocabulary__topic_id=topic_id,
            mastery_level__lt=5 # Chỉ lấy thẻ chưa thuộc lòng (level < 5)
        ).exclude(
            id__in=excluded_card_ids # Loại bỏ thẻ đã học trong phiên
        ).select_related('vocabulary', 'vocabulary__topic') # Join bảng để lấy dữ liệu luôn

        # Sắp xếp: 
        # 1. last_reviewed là NULL lên đầu (nulls_first=True)
        # 2. last_reviewed tăng dần (cũ nhất lên trước)
        candidate_card = queryset.order_by(
            F('last_reviewed').asc(nulls_first=True)
        ).first()

        if not candidate_card:
            return None # Hết bài

        # Format dữ liệu trả về (gọi hàm helper bên dưới)
        return StudyService.generate_question_data(candidate_card)

    # --- 2. TẠO DỮ LIỆU CÂU HỎI ---
    @staticmethod
    def generate_question_data(card_obj):
        """
        Input: Flashcard Object (ORM)
        Output: Dictionary cho API
        """
        vocab = card_obj.vocabulary
        
        # Logic chọn loại câu hỏi
        has_audio = bool(vocab.audio)
        q_type = 'listening' if has_audio and random.choice([True, False]) else 'fill_blank'
        
        # Xây dựng URL
        image_url = vocab.topic.image.url if vocab.topic.image else ""
        audio_url = vocab.audio.url if vocab.audio else ""

        data = {
            'card_id': card_obj.id,
            'vocabulary_id': vocab.id,
            'type': q_type,
            'word': vocab.word,
            'phonetic': vocab.phonetic,
            'definition': vocab.definition,
            'meaning': vocab.meaning_sentence,
            'image': image_url,
            'audio': audio_url,
            'instruction': "",
            'content': ""
        }

        if q_type == 'fill_blank':
            data['instruction'] = f"Điền từ nghĩa là: '{vocab.meaning_sentence}'"
            example = vocab.example_sentence
            if example:
                # Masking từ vựng: thay 'apple' thành '_____'
                masked = re.sub(re.escape(vocab.word), '_' * len(vocab.word), example, flags=re.IGNORECASE)
                data['content'] = masked
            else:
                data['content'] = "_" * len(vocab.word)
        else:
            data['instruction'] = "Nghe và viết lại từ vựng"
            data['content'] = "Listen carefully"

        return data

    # --- 3. CHẤM ĐIỂM ---
    @staticmethod
    def check_answer(user, card_id, user_answer):
        try:
            # 1. Lấy thẻ từ DB
            card = Flashcard.objects.select_related('vocabulary').get(id=card_id, user=user)
            vocab = card.vocabulary
            
            # 2. So sánh đáp án
            is_correct = user_answer.strip().lower() == vocab.word.strip().lower()
            current_level = card.mastery_level
            new_level = current_level

            # 3. Tính điểm mới
            if is_correct:
                if current_level < 5: new_level += 1
            else:
                if current_level > 0: new_level -= 1
            
            # 4. Update Database
            if new_level != current_level:
                card.mastery_level = new_level
                
            # Luôn cập nhật thời gian ôn tập
            card.last_reviewed = timezone.now()
            card.save()

            # 5. Lưu Log
            StudyLog.objects.create(
                user=user,
                vocabulary=vocab,
                is_correct=is_correct,
                answered_at=timezone.now()
            )

            return {
                'is_correct': is_correct,
                'new_level': new_level,
                'word': vocab.word,
                'phonetic': vocab.phonetic,
                'meaning': vocab.meaning_sentence,
                'audio': vocab.audio.url if vocab.audio else ""
            }

        except Flashcard.DoesNotExist:
            return {'error': 'Không tìm thấy thẻ học'}

    # --- 4. THỐNG KÊ & TIỆN ÍCH ---
    @staticmethod
    def get_stats(user):
        """Lấy thống kê dashboard"""
        # Đếm tổng thể
        total_answers = StudyLog.objects.filter(user=user).count()
        correct_answers = StudyLog.objects.filter(user=user, is_correct=True).count()
        
        # Tính độ chính xác
        accuracy = int((correct_answers / total_answers * 100)) if total_answers > 0 else 0
        
        # Đếm số từ đã thuộc (level >= 3)
        mastered_count = Flashcard.objects.filter(user=user, mastery_level__gte=3).count()
        
        # Đếm tổng số từ đang học
        total_words = Flashcard.objects.filter(user=user).count()

        return {
            'total_answers': total_answers,
            'accuracy': accuracy,
            'mastered_count': mastered_count,
            'total_words': total_words,
            # Streak cần bảng riêng hoặc logic phức tạp hơn, tạm để 0
            'streak': 0 
        }

    @staticmethod
    def reset_topic_progress(user, topic_id):
        """Reset toàn bộ thẻ của 1 topic về 0"""
        Flashcard.objects.filter(
            user=user, 
            vocabulary__topic_id=topic_id
        ).update(
            mastery_level=0, 
            last_reviewed=None
        )