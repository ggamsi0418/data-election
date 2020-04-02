from django.contrib import admin
from django.urls import path, include
from fileManage import views

urlpatterns = [
    path("", views.index),
    path("upload/", views.upload),
    path("verify/", views.djangoServer),
]
