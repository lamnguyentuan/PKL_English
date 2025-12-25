"""
Service xử lý logic thẻ học (Flashcard)
- Lấy thẻ học
- Tạo câu hỏi
- Chấm điểm
"""
from django.db import connection
import random
import re
from .utils import dictfetchall


class FlashcardService:

    # --- 1. LẤY THẺ HỌC ---
    @staticmethod
    def get_learning_card(user, topic_id, excluded_card_ids=None):
        """
        Lấy 1 thẻ để học.
        excluded_card_ids: danh sách card_id đã học trong phiên (để không lặp lại)
        """
        if excluded_card_ids is None:
            excluded_card_ids = []
        
        with connection.cursor() as cursor:
            # BƯỚC A: ĐỒNG BỘ DỮ LIỆU (Sync)
            # 1. Lấy tất cả ID từ vựng của Topic này
            cursor.execute("SELECT id FROM study_vocabulary WHERE topic_id = %s", [topic_id])
            vocab_rows = cursor.fetchall()
            all_vocab_ids = set([row[0] for row in vocab_rows])

            # 2. Lấy tất cả ID từ vựng mà User ĐÃ CÓ thẻ
            cursor.execute("""
                SELECT vocabulary_id FROM study_flashcard 
                WHERE user_id = %s 
                AND vocabulary_id IN (SELECT id FROM study_vocabulary WHERE topic_id = %s)
            """, [user.id, topic_id])
            existing_rows = cursor.fetchall()
            existing_vocab_ids = set([row[0] for row in existing_rows])

            # 3. Tìm cái còn thiếu
            missing_ids = all_vocab_ids - existing_vocab_ids

            # 4. Tạo thẻ mới bằng lệnh INSERT (Nếu có thiếu)
            for vid in missing_ids:
                cursor.execute("""
                    INSERT INTO study_flashcard (user_id, vocabulary_id, mastery_level)
                    VALUES (%s, %s, 0) 
                """, [user.id, vid]) 

            # BƯỚC B: LẤY 1 THẺ ĐỂ HỌC (Ưu tiên từ chưa ôn gần đây)
            # Thứ tự ưu tiên:
            # 1. Từ chưa bao giờ ôn (last_reviewed IS NULL)
            # 2. Từ ôn lâu nhất (last_reviewed cũ nhất)
            # 3. Random trong nhóm cùng thời gian
            
            # Tạo điều kiện loại bỏ card đã học trong phiên
            exclude_condition = ""
            params = [user.id, topic_id]
            
            if excluded_card_ids:
                placeholders = ','.join(['%s'] * len(excluded_card_ids))
                exclude_condition = f"AND fc.id NOT IN ({placeholders})"
                params.extend(excluded_card_ids)
            
            sql = f"""
                SELECT 
                    fc.id as card_id,
                    fc.mastery_level,
                    v.id as vocabulary_id,
                    v.word,
                    v.phonetic,
                    v.definition,
                    v.meaning_sentence as meaning,
                    v.audio,
                    v.example_sentence,
                    t.image as topic_image
                FROM study_flashcard fc
                JOIN study_vocabulary v ON fc.vocabulary_id = v.id
                JOIN study_topic t ON v.topic_id = t.id
                WHERE fc.user_id = %s 
                AND v.topic_id = %s
                AND fc.mastery_level < 5
                {exclude_condition}
                ORDER BY 
                    fc.last_reviewed IS NULL DESC,
                    fc.last_reviewed ASC,
                    RAND()
                LIMIT 1
            """

            cursor.execute(sql, params)
            result = dictfetchall(cursor)

            if not result:
                return None # Hết bài học
            
            return result[0] # Trả về dictionary của thẻ đầu tiên tìm được

    # --- 2. TẠO DỮ LIỆU CÂU HỎI ---
    @staticmethod
    def generate_question_data(card_data):
        # card_data bây giờ là dictionary do hàm SQL trên trả về
        
        # Xử lý đường dẫn ảnh/audio (Vì SQL chỉ trả về chuỗi text)
        audio_url = f"/media/{card_data['audio']}" if card_data['audio'] else ""
        image_url = f"/media/{card_data['topic_image']}" if card_data['topic_image'] else ""

        # Logic tạo câu hỏi 
        q_type = 'fill_blank' if not card_data['audio'] or random.choice([True, False]) else 'listening'

        data = {
            'card_id': card_data['card_id'],
            'vocabulary_id': card_data['vocabulary_id'],  
            'type': q_type,
            'word': card_data['word'],
            'phonetic': card_data['phonetic'],
            'definition': card_data['definition'],
            'meaning': card_data['meaning'],
            'image': image_url,
            'audio': audio_url,
            'instruction': "",
            'content': ""
        }

        if q_type == 'fill_blank':
            data['instruction'] = f"Điền từ nghĩa là: '{card_data['meaning']}'"
            example = card_data['example_sentence']
            word = card_data['word']
            if example:
                masked = re.sub(re.escape(word), '_' * len(word), example, flags=re.IGNORECASE)
                data['content'] = masked
            else:
                data['content'] = "_" * len(word)
        else:
            data['instruction'] = "Nghe và viết lại từ vựng"
            data['content'] = "Listen carefully"

        return data

    # --- 3. CHẤM ĐIỂM ---
    @staticmethod
    def check_answer(user, card_id, user_answer):
        with connection.cursor() as cursor:
            # 1. Lấy thông tin đúng từ DB để so sánh
            cursor.execute("""
                SELECT fc.mastery_level, fc.vocabulary_id, v.word, v.meaning_sentence, v.phonetic, v.audio 
                FROM study_flashcard fc
                JOIN study_vocabulary v ON fc.vocabulary_id = v.id
                WHERE fc.id = %s AND fc.user_id = %s
            """, [card_id, user.id])
            
            row = dictfetchall(cursor)
            if not row: return None
            
            card_info = row[0]
            current_level = card_info['mastery_level']
            correct_word = card_info['word']
            vocabulary_id = card_info['vocabulary_id']

            # 2. So sánh đáp án
            is_correct = user_answer.strip().lower() == correct_word.strip().lower()
            new_level = current_level

            # 3. Tính điểm mới
            if is_correct:
                if current_level < 5: new_level += 1
            else:
                if current_level > 0: new_level -= 1

            # 4. UPDATE lại vào Database 
            if new_level != current_level:
                cursor.execute("""
                    UPDATE study_flashcard 
                    SET mastery_level = %s, last_reviewed = NOW()
                    WHERE id = %s
                """, [new_level, card_id])

            # 5. Lưu log thống kê
            cursor.execute("""
                INSERT INTO study_studylog (user_id, vocabulary_id, is_correct, answered_at)
                VALUES (%s, %s, %s, NOW())
            """, [user.id, vocabulary_id, is_correct])

            return {
                'is_correct': is_correct,
                'new_level': new_level,
                'word': correct_word,
                'phonetic': card_info['phonetic'],
                'meaning': card_info['meaning_sentence'],
                'audio': f"/media/{card_info['audio']}" if card_info['audio'] else ""
            }

    # --- 4. TIẾN ĐỘ TOPIC ---
    @staticmethod
    def get_topic_progress(user, topic_id):
        with connection.cursor() as cursor:
            # Lấy tổng số từ vựng trong topic
            cursor.execute("SELECT COUNT(id) FROM study_vocabulary WHERE topic_id = %s", [topic_id])
            total_vocab = cursor.fetchone()[0]

            if total_vocab == 0:
                return 0

            # Lấy số từ vựng đã thuộc (mastery_level >= 3)
            cursor.execute("""
                SELECT COUNT(fc.id)
                FROM study_flashcard fc
                JOIN study_vocabulary v ON fc.vocabulary_id = v.id
                WHERE fc.user_id = %s AND v.topic_id = %s AND fc.mastery_level >= 3
            """, [user.id, topic_id])
            mastered_count = cursor.fetchone()[0]

            progress = int((mastered_count / total_vocab) * 100)
            return progress

    @staticmethod
    def count_cards_to_learn(user, topic_id):
        """Đếm số thẻ cần học (level < 5)"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(fc.id)
                FROM study_flashcard fc
                JOIN study_vocabulary v ON fc.vocabulary_id = v.id
                WHERE fc.user_id = %s AND v.topic_id = %s AND fc.mastery_level < 5
            """, [user.id, topic_id])
            return cursor.fetchone()[0]

    @staticmethod
    def reset_topic_progress(user, topic_id):
        """Reset tiến độ học của 1 topic về level 0"""
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE study_flashcard fc
                JOIN study_vocabulary v ON fc.vocabulary_id = v.id
                SET fc.mastery_level = 0, fc.last_reviewed = NULL
                WHERE fc.user_id = %s AND v.topic_id = %s
            """, [user.id, topic_id])
            return {'status': 'reset', 'message': 'Đã reset tiến độ'}
