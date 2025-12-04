# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('create/', views.PostCreateView.as_view(), name='create_post'),
    path('export/', views.export_selected_pdf, name='export_selected_pdf'),
    path('generate-exam/', views.generate_exam_pdf, name='generate_exam_pdf'),
]