from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.index),
    path('group_list.html', views.group_list),
]
