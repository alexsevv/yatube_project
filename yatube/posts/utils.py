from django.core.paginator import Paginator

COUNT_POSTS = 10


def use_paginator(request, list):
    paginator = Paginator(list, COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
