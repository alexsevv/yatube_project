from django.http import HttpResponse


def index(request):
    return HttpResponse('Главнейшая страница')


def group_posts(request, slug):
    return HttpResponse(f"""здесь будет название определенной группы. А это имя
                        текущей группы: {slug}"""
                        )
