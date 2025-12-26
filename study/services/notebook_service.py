import random
import re
from django.db.models import Count
from study.models import NotebookEntry, Vocabulary # Import đúng Model

class NotebookService:
    """
    Service này chỉ chứa LOGIC NGHIỆP VỤ PHỨC TẠP (Business Logic).
    Các thao tác CRUD cơ bản (Thêm/Sửa/Xóa/List) đã được ViewSet xử lý.
    """

    @staticmethod
    def get_notebook_review_question(user, excluded_vocab_ids=None):
        """
        Lấy 1 câu hỏi ôn tập từ sổ tay.
        """
        if excluded_vocab_ids is None:
            excluded_vocab_ids = []

        # --- 1. LẤY DỮ LIỆU (Dùng ORM) ---
        # select_related('vocabulary') giúp lấy luôn thông tin từ vựng trong 1 câu query (tối ưu SQL)
        entries = NotebookEntry.objects.filter(user=user).select_related('vocabulary')
        
        # Chuyển QuerySet thành list các object Vocabulary
        all_vocabs = [entry.vocabulary for entry in entries]

        if len(all_vocabs) < 2:
            return None  # Cần ít nhất 2 từ để tạo đáp án nhiễu

        # Lọc bỏ các từ đã ôn (excluded)
        available_vocabs = [v for v in all_vocabs if v.id not in excluded_vocab_ids]
        
        if not available_vocabs:
            return None # Hết từ để ôn

        # --- 2. XỬ LÝ LOGIC CHỌN CÂU HỎI (Logic cũ) ---
        vocabs_with_audio = [v for v in available_vocabs if v.audio]
        vocabs_word = [v for v in available_vocabs if v.word]

        # Random loại câu hỏi
        if vocabs_with_audio and vocabs_word:
            q_type = random.choice(['listening', 'fill_blank'])
            correct_vocab = random.choice(vocabs_with_audio if q_type == 'listening' else vocabs_word)
        elif vocabs_with_audio:
            q_type = 'listening'
            correct_vocab = random.choice(vocabs_with_audio)
        elif vocabs_word:
            q_type = 'fill_blank'
            correct_vocab = random.choice(vocabs_word)
        else:
            # Fallback nếu dữ liệu thiếu
            correct_vocab = random.choice(available_vocabs)
            q_type = 'fill_blank' 

        # --- 3. ĐÓNG GÓI DỮ LIỆU TRẢ VỀ ---
        # Lưu ý: Ở đây dùng thuộc tính object (v.word) chứ không phải dict (v['word'])
        result = {
            'vocabulary_id': correct_vocab.id,
            'word': correct_vocab.word,
            'phonetic': correct_vocab.phonetic,
            'meaning': correct_vocab.meaning_sentence,
            'definition': correct_vocab.definition or correct_vocab.meaning_sentence,
            'audio': correct_vocab.audio.url if correct_vocab.audio else "",
            'type': q_type
        }

        if q_type == 'listening':
            # Chọn đáp án sai từ danh sách còn lại
            other_vocabs = [v for v in all_vocabs if v.id != correct_vocab.id]
            wrong_options = random.sample(other_vocabs, min(len(other_vocabs), 3))
            
            options = [{
                'vocabulary_id': correct_vocab.id,
                'word': correct_vocab.word,
                'is_correct': True
            }]
            
            for v in wrong_options:
                options.append({
                    'vocabulary_id': v.id,
                    'word': v.word,
                    'is_correct': False
                })
            
            random.shuffle(options)
            result['options'] = options
            result['instruction'] = 'Nghe và chọn đáp án đúng'
            
        else: # fill_blank
            example = correct_vocab.example_sentence
            word = correct_vocab.word
            # Masking từ vựng trong câu ví dụ
            masked = re.sub(re.escape(word), '_' * len(word), example, flags=re.IGNORECASE)
            
            result['content'] = masked
            result['instruction'] = f"Điền từ nghĩa là: '{correct_vocab.meaning_sentence}'"

        return result

    @staticmethod
    def count_notebook_reviewable(user):
        """Đếm số từ trong notebook"""
        return NotebookEntry.objects.filter(user=user).count()

    @staticmethod
    def check_fill_blank_review(vocabulary_id, user_answer):
        """Kiểm tra đáp án điền từ"""
        try:
            vocab = Vocabulary.objects.get(id=vocabulary_id)
            is_correct = user_answer.strip().lower() == vocab.word.strip().lower()
            return {'is_correct': is_correct}
        except Vocabulary.DoesNotExist:
            return {'is_correct': False}