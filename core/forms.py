from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'area_do_conhecimento', 'dificuldade']
        widgets = {
            'content': SummernoteWidget(),
        }
