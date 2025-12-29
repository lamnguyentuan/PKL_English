from django import forms
from .models import Topic, Vocabulary

class MyTopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["title", "description", "image"]

class MyVocabularyForm(forms.ModelForm):
    class Meta:
        model = Vocabulary
        fields = ["word", "phonetic", "definition", "example_sentence", "meaning_sentence", "audio"]
