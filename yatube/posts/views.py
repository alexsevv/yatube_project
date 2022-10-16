from django.http import HttpResponse


def index(request):
    return HttpResponse('Главнейшая страница')


def group_posts(request, slug):
    return HttpResponse(f"""здесь будут определенной группы. А это имя
                        текущей группы: {slug}"""
                        )
