# teacher_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_view, name='teacher'),
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
]