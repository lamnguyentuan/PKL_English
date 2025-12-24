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
            result = StudyService.dictfetchall(cursor)

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

        # Logic tạo câu hỏi (như cũ)
        q_type = 'fill_blank' if not card_data['audio'] or random.choice([True, False]) else 'listening'

        data = {
            'card_id': card_data['card_id'],
            'vocabulary_id': card_data['vocabulary_id'],  
            'type': q_type,
            'word': card_data['word'],
            'phonetic': card_data['phonetic'],
            'definition': card_data['definition'],  # THÊM DÒNG NÀY
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
            
            row = StudyService.dictfetchall(cursor)
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

    # --- 4. THỐNG KÊ ---
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

    #5. Tính prrogress của topic
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

    # --- 6. SỔ TAY TỪ VỰNG ---
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
            return StudyService.dictfetchall(cursor)

    # --- 7. ÔN TẬP SỔ TAY ---
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
                    v.audio
                FROM study_notebookentry nb
                JOIN study_vocabulary v ON nb.vocabulary_id = v.id
                WHERE nb.user_id = %s
            """, [user.id])
            all_vocabs = StudyService.dictfetchall(cursor)
            
            if len(all_vocabs) < 2:
                return None  # Cần ít nhất 2 từ để tạo câu hỏi
            
            # Lọc bỏ các từ đã ôn trong phiên
            available_vocabs = [v for v in all_vocabs if v['vocabulary_id'] not in excluded_vocab_ids]
            
            if not available_vocabs:
                return None  # Hết từ để ôn
            
            # Chọn ngẫu nhiên 1 từ làm câu hỏi chính
            # Ưu tiên từ có audio cho listening
            vocabs_with_audio = [v for v in available_vocabs if v['audio'] and v['audio'] != '']
            vocabs_with_example = [v for v in available_vocabs if v['example_sentence'] and v['example_sentence'] != '']
            
            # Ưu tiên random giữa 2 loại nếu cả 2 đều có từ phù hợp
            if vocabs_with_audio and vocabs_with_example:
                q_type = random.choice(['listening', 'fill_blank'])
                if q_type == 'listening':
                    correct_vocab = random.choice(vocabs_with_audio)
                else:
                    correct_vocab = random.choice(vocabs_with_example)
            elif vocabs_with_audio:
                q_type = 'listening'
                correct_vocab = random.choice(vocabs_with_audio)
            elif vocabs_with_example:
                q_type = 'fill_blank'
                correct_vocab = random.choice(vocabs_with_example)
            else:
                # Không có từ phù hợp
                correct_vocab = random.choice(available_vocabs)
                q_type = 'fill_blank'  # Fallback
            
            result = {
                'vocabulary_id': correct_vocab['vocabulary_id'],
                'word': correct_vocab['word'],
                'phonetic': correct_vocab['phonetic'],
                'meaning': correct_vocab['meaning_sentence'],
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
                    'meaning': correct_vocab['meaning_sentence'],
                    'is_correct': True
                }]
                
                for v in wrong_options:
                    options.append({
                        'vocabulary_id': v['vocabulary_id'],
                        'meaning': v['meaning_sentence'],
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

    # --- 8. THỐNG KÊ CHI TIẾT ---
    @staticmethod
    def log_answer(user, vocabulary_id, is_correct):
        """Lưu log mỗi lần trả lời"""
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO study_studylog (user_id, vocabulary_id, is_correct, answered_at)
                VALUES (%s, %s, %s, NOW())
            """, [user.id, vocabulary_id, is_correct])

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
            stats['daily_stats'] = StudyService.dictfetchall(cursor)
            
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
            stats['most_wrong'] = StudyService.dictfetchall(cursor)
            
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
            from datetime import date, timedelta
            today = date.today()
            
            for i, d in enumerate(dates):
                expected_date = today - timedelta(days=i)
                if d == expected_date:
                    streak += 1
                else:
                    break
            
            stats['streak'] = streak
            
            return stats