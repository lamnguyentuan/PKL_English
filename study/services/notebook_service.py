"""
Service xử lý logic Sổ tay từ vựng (Notebook)
- Thêm/xóa/sửa từ trong sổ tay
- Ôn tập sổ tay
"""
from django.db import connection
import random
import re
from .utils import dictfetchall


class NotebookService:

    # --- 1. QUẢN LÝ SỔ TAY ---
    @staticmethod
    def add_to_notebook(user, vocabulary_id, note=""):
        """Thêm từ vựng vào sổ tay"""
        with connection.cursor() as cursor:
            # Kiểm tra đã tồn tại chưa
            cursor.execute("""
                SELECT id FROM study_notebookentry 
                WHERE user_id = %s AND vocabulary_id = %s
            """, [user.id, vocabulary_id])
            existing = cursor.fetchone()
            
            if existing:
                return {'status': 'exists', 'message': 'Từ đã có trong sổ tay'}
            
            # Thêm mới
            cursor.execute("""
                INSERT INTO study_notebookentry (user_id, vocabulary_id, note, added_at)
                VALUES (%s, %s, %s, NOW())
                """, [user.id, vocabulary_id, note])
            return {'status': 'created', 'message': 'Đã lưu vào sổ tay'}

    @staticmethod
    def remove_from_notebook(user, vocabulary_id):
        """Xóa từ vựng khỏi sổ tay"""
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM study_notebookentry 
                WHERE user_id = %s AND vocabulary_id = %s
            """, [user.id, vocabulary_id])
            return {'status': 'deleted'}

    @staticmethod
    def update_notebook_note(user, vocabulary_id, note):
        """Cập nhật ghi chú"""
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE study_notebookentry 
                SET note = %s 
                WHERE user_id = %s AND vocabulary_id = %s
            """, [note, user.id, vocabulary_id])
            return {'status': 'updated'}

    @staticmethod
    def get_notebook(user):
        """Lấy danh sách sổ tay của user"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    nb.id as entry_id,
                    nb.note,
                    nb.added_at,
                    v.id as vocabulary_id,
                    v.word,
                    v.phonetic,
                    v.meaning_sentence,
                    v.audio,
                    t.title as topic_title
                FROM study_notebookentry nb
                JOIN study_vocabulary v ON nb.vocabulary_id = v.id
                JOIN study_topic t ON v.topic_id = t.id
                WHERE nb.user_id = %s
                ORDER BY nb.added_at DESC
            """, [user.id])
            return dictfetchall(cursor)

    # --- 2. ÔN TẬP SỔ TAY ---
    @staticmethod
    def get_notebook_review_question(user, excluded_vocab_ids=None):
        """
        Lấy 1 câu hỏi ôn tập từ sổ tay.
        Có 2 loại: listening (nghe chọn đáp án) và fill_blank (điền từ vào chỗ trống)
        """
        if excluded_vocab_ids is None:
            excluded_vocab_ids = []
        
        with connection.cursor() as cursor:
            # Lấy tất cả từ trong notebook
            cursor.execute("""
                SELECT 
                    v.id as vocabulary_id,
                    v.word,
                    v.phonetic,
                    v.meaning_sentence,
                    v.example_sentence,
                    v.definition,
                    v.audio
                FROM study_notebookentry nb
                JOIN study_vocabulary v ON nb.vocabulary_id = v.id
                WHERE nb.user_id = %s
            """, [user.id])
            all_vocabs = dictfetchall(cursor)
            
            if len(all_vocabs) < 2:
                return None  # Cần ít nhất 2 từ để tạo câu hỏi
            
            # Lọc bỏ các từ đã ôn trong phiên
            available_vocabs = [v for v in all_vocabs if v['vocabulary_id'] not in excluded_vocab_ids]
            
            if not available_vocabs:
                return None  # Hết từ để ôn
            
            # Chọn ngẫu nhiên 1 từ làm câu hỏi chính
            # Ưu tiên từ có audio cho listening
            vocabs_with_audio = [v for v in available_vocabs if v['audio'] and v['audio'] != '']
            vocabs_word = [v for v in available_vocabs if v['word'] and v['word'] != '']
            
            # Ưu tiên random giữa 2 loại nếu cả 2 đều có từ phù hợp
            if vocabs_with_audio and vocabs_word:
                q_type = random.choice(['listening', 'fill_blank'])
                if q_type == 'listening':
                    correct_vocab = random.choice(vocabs_with_audio)
                else:
                    correct_vocab = random.choice(vocabs_word)
            elif vocabs_with_audio:
                q_type = 'listening'
                correct_vocab = random.choice(vocabs_with_audio)
            elif vocabs_word:
                q_type = 'fill_blank'
                correct_vocab = random.choice(vocabs_word)
            else:
                # Không có từ phù hợp
                correct_vocab = random.choice(available_vocabs)
                q_type = 'fill_blank'  # Fallback
            
            result = {
                'vocabulary_id': correct_vocab['vocabulary_id'],
                'word': correct_vocab['word'],
                'phonetic': correct_vocab['phonetic'],
                'meaning': correct_vocab['meaning_sentence'],
                'definition': correct_vocab.get('definition', correct_vocab['meaning_sentence']),
                'audio': f"/media/{correct_vocab['audio']}" if correct_vocab['audio'] else "",
                'type': q_type
            }
            
            if q_type == 'listening':
                # Tạo các đáp án sai (lấy từ các từ khác)
                other_vocabs = [v for v in all_vocabs if v['vocabulary_id'] != correct_vocab['vocabulary_id']]
                wrong_options = random.sample(other_vocabs, min(len(other_vocabs), 3))
                
                # Tạo danh sách đáp án và xáo trộn
                options = [{
                    'vocabulary_id': correct_vocab['vocabulary_id'],
                    'word': correct_vocab['word'],
                    'is_correct': True
                }]
                
                for v in wrong_options:
                    options.append({
                        'vocabulary_id': v['vocabulary_id'],
                        'word': v['word'],
                        'is_correct': False
                    })
                
                random.shuffle(options)
                result['options'] = options
                result['instruction'] = 'Nghe và chọn đáp án đúng'
                
            else:  # fill_blank
                # Tạo câu có chỗ trống
                example = correct_vocab['example_sentence']
                word = correct_vocab['word']
                masked = re.sub(re.escape(word), '_' * len(word), example, flags=re.IGNORECASE)
                result['content'] = masked
                result['instruction'] = f"Điền từ nghĩa là: '{correct_vocab['meaning_sentence']}'"
            
            return result

    @staticmethod
    def count_notebook_reviewable(user):
        """Đếm số từ trong notebook có thể ôn tập"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(nb.id)
                FROM study_notebookentry nb
                JOIN study_vocabulary v ON nb.vocabulary_id = v.id
                WHERE nb.user_id = %s
            """, [user.id])
            return cursor.fetchone()[0]

    @staticmethod
    def check_review_answer(vocabulary_id, selected_vocab_id):
        """Kiểm tra đáp án ôn tập (listening)"""
        is_correct = int(vocabulary_id) == int(selected_vocab_id)
        return {'is_correct': is_correct}

    @staticmethod
    def check_fill_blank_review(vocabulary_id, user_answer):
        """Kiểm tra đáp án ôn tập (fill_blank)"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT word FROM study_vocabulary WHERE id = %s
            """, [vocabulary_id])
            row = cursor.fetchone()
            if not row:
                return {'is_correct': False}
            
            correct_word = row[0]
            is_correct = user_answer.strip().lower() == correct_word.strip().lower()
            return {'is_correct': is_correct}
