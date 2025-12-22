from django.db import connection
import random
import re

class StudyService:

    # --- HÀM PHỤ TRỢ: CHUYỂN SQL THÀNH DICTIONARY ---
    @staticmethod
    def dictfetchall(cursor):
        """
        Hàm này giúp biến kết quả thô của SQL (dạng Tuples)
        thành dạng Dictionary (có key, value) để dễ code.
        """
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    # --- 1. LẤY THẺ HỌC (Thay thế get_learning_card) ---
    @staticmethod
    def get_learning_card(user, topic_id):
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
                # Lưu ý: datetime('now') là cú pháp SQLite. Nếu dùng MySQL thì dùng NOW()

            # BƯỚC B: LẤY 1 THẺ NGẪU NHIÊN ĐỂ HỌC   
            # Lấy thẻ chưa thuộc (level < 5) và random
            sql = """
                SELECT 
                    fc.id as card_id,
                    fc.mastery_level,
                    v.word,
                    v.phonetic,
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
                ORDER BY RAND() 
                LIMIT 1
            """
            # Lưu ý: ORDER BY RANDOM() là của SQLite/PostgreSQL. 
            # Nếu bạn dùng MySQL thì đổi thành ORDER BY RAND()
            
            cursor.execute(sql, [user.id, topic_id])
            result = StudyService.dictfetchall(cursor)

            if not result:
                return None # Hết bài học
            
            return result[0] # Trả về dictionary của thẻ đầu tiên tìm được

    # --- 2. TẠO DỮ LIỆU CÂU HỎI (Logic Python giữ nguyên) ---
    @staticmethod
    def generate_question_data(card_data):
        # card_data bây giờ là dictionary do hàm SQL trên trả về
        # Ta truy cập bằng ['key'] thay vì .key
        
        # Xử lý đường dẫn ảnh/audio (Vì SQL chỉ trả về chuỗi text)
        audio_url = f"/media/{card_data['audio']}" if card_data['audio'] else ""
        image_url = f"/media/{card_data['topic_image']}" if card_data['topic_image'] else ""

        # Logic tạo câu hỏi (như cũ)
        q_type = 'fill_blank' if not card_data['audio'] or random.choice([True, False]) else 'listening'

        data = {
            'card_id': card_data['card_id'],
            'type': q_type,
            'word': card_data['word'],
            'phonetic': card_data['phonetic'],
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

    # --- 3. CHẤM ĐIỂM (Thay thế check_answer) ---
    @staticmethod
    def check_answer(user, card_id, user_answer):
        with connection.cursor() as cursor:
            # 1. Lấy thông tin đúng từ DB để so sánh
            cursor.execute("""
                SELECT fc.mastery_level, v.word, v.meaning_sentence, v.phonetic, v.audio 
                FROM study_flashcard fc
                JOIN study_vocabulary v ON fc.vocabulary_id = v.id
                WHERE fc.id = %s AND fc.user_id = %s
            """, [card_id, user.id])
            
            row = StudyService.dictfetchall(cursor)
            if not row: return None
            
            card_info = row[0]
            current_level = card_info['mastery_level']
            correct_word = card_info['word']

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
                    SET mastery_level = %s, updated_at = datetime('now')
                    WHERE id = %s
                """, [new_level, card_id])

            return {
                'is_correct': is_correct,
                'new_level': new_level,
                'word': correct_word,
                'phonetic': card_info['phonetic'],
                'meaning': card_info['meaning_sentence'],
                'audio': f"/media/{card_info['audio']}" if card_info['audio'] else ""
            }

    # --- 4. THỐNG KÊ (Thay thế get_stats) ---
    @staticmethod
    def get_stats(user):
        with connection.cursor() as cursor:
            # Câu lệnh GROUP BY thần thánh của SQL
            # Đếm xem mỗi level có bao nhiêu thẻ
            cursor.execute("""
                SELECT mastery_level, COUNT(id) as count
                FROM study_flashcard
                WHERE user_id = %s
                GROUP BY mastery_level
            """, [user.id])
            
            rows = cursor.fetchall() # Trả về dạng [(0, 5), (1, 2)...]

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