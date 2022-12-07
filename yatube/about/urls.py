from django.urls import path

from . import views


app_name = 'about'

urlpatterns = [
    path('author/', views.AuthorPage.as_view(), name='author'),
    path('tech/', views.TechPage.as_view(), name='tech'),
    path('my_code/', views.MyCode.as_view(), name='my_code'),
]
