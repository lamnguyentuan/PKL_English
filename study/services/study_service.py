from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from study.models import Topic, Vocabulary, Flashcard
import random
import re

class StudyService:
    @staticmethod
    #Lấy danh sách tất cả chủ đề
    def get_all_topics():
        return Topic.objects.all()
    
    @staticmethod
    def get_random_flashcard(user, topic_id):

    #Lấy thẻ ngẫu nhiên level < 5
        vocab_ids = Vocabulary.objects.filter(topic_id=topic_id).values_list('id', flat=True)
        existing_vocab_ids = Flashcard.objects.filter(user=user, vocabulary_id__in=vocab_ids).values_list('vocabulary_id', flat=True)
        missing_ids = set(vocab_ids) - set(existing_vocab_ids)

        if missing_ids:
            Flashcard.objects.bulk_create([
                Flashcard(user=user, vocabulary_id=vid, mastery_level=0) for vid in missing_ids
            ])

        card = Flashcard.objects.filter(
            user=user,
            vocabulary__topic_id=topic_id,
            mastery_level__lt=5
        ).order_by('?').first()
        return card
    @staticmethod
    def generate_question_for_flashcard(flashcard):
       vocab = flashcard.vocabulary
       question_type = random.choice(['fill_blank', 'listening']) if vocab.audio else 'fill_blank'
       data = {
            'card_id': flashcard.id,
            'type': question_type,
            'audio': vocab.audio.url if vocab.audio else None,
            'image': vocab.topic.image.url if vocab.topic.image else None, # Lấy tạm ảnh topic
            'word_length': len(vocab.word)
       }
       if question_type == 'fill_blank':
          data['instruction'] = f"Hãy điền từ vựng vào chỗ trống: {vocab.meaning_sentence}"
          if vocab.meaning_sentence:
              blank_sentence = re.sub(re.escape(vocab.word), '_'*len(vocab.word), vocab.meaning_sentence, flags=re.IGNORECASE)
              data['sentence'] = blank_sentence
          else:
              data['sentence'] = '_' * len(vocab.word)
       else:
          data['instruction'] = "Hãy nghe và viết lại từ bạn nghe được."
          data['sentence'] = None
       return data
    @staticmethod
    def check_answer(user, flashcard_id, answer):
        try:
            flashcard = Flashcard.objects.get(id=flashcard_id, user=user)
        except Flashcard.DoesNotExist:
            return {'error': 'Flashcard not found.'}

        correct_word = flashcard.vocabulary.word
        is_correct = (answer.strip().lower() == correct_word.strip().lower())

        if is_correct:
            flashcard.mastery_level = min(flashcard.mastery_level + 1, 5)
        else:
            flashcard.mastery_level = max(flashcard.mastery_level - 1, 0)

        flashcard.last_reviewed = timezone.now()
        flashcard.save()

        return {
            'is_correct': is_correct,
            'correct_word': correct_word,
            'new_mastery_level': flashcard.mastery_level
        }
    @staticmethod
    def get_stats(user):
        stats = Flashcard.objects.filter(user=user).values('mastery_level').annotate(count=Count('id')).order_by('mastery_level')
        result = {level: 0 for level in range(6)}
        total_learned = 0 # Số thẻ đã học (mastery_level > 0)
        for item in stats:
            level = item['mastery_level']
            count = item['count']
            result[level] = count
            if level > 0:
                total_learned += count

        return {
            'level_counts': result,
            'total_learned': total_learned
        }