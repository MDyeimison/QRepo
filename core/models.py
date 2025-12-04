# core/models.py
from django.db import models
from colorfield.fields import ColorField


class AreaDoConhecimento(models.Model):
    name = models.CharField(max_length=200)
    color = ColorField(default='#3498db', help_text="Choose a color")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Dificuldade(models.Model):
    name = models.CharField(max_length=200)
    color = ColorField(default='#3498db', help_text="Choose a color")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    area_do_conhecimento = models.ForeignKey(AreaDoConhecimento, on_delete=models.SET_NULL, null=True, blank=True)
    dificuldade = models.ForeignKey(Dificuldade, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title