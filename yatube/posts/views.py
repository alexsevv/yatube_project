# from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    template = 'posts/index.html'
    title = "Последние обновления на сайте"
    text = "Это главная страница проекта Yatube"
    context = {
        'title': title,
        'text': text,
    }
    return render(request, template, context)


def group_list(request):
    template = 'posts/group_list.html'
    title = "Лев Толстой – зеркало русской революции."
    text = "Здесь будет информация о группах проекта Yatube"
    context = {
        'title': title,
        'text': text,
    }
    return render(request, template, context)
