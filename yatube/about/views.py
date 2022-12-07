from django.views.generic.base import TemplateView


class AuthorPage(TemplateView):
    template_name = 'about/author_page.html'


class TechPage(TemplateView):
    template_name = 'about/tech_page.html'


class MyCode(TemplateView):
    template_name = 'about/my_code.html'
