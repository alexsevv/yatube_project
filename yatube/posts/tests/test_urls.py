from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group


User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlTest.user)
        cache.clear()

    def test_urls_response_guest(self):
        """Статус страниц для гостя."""
        url_status = [
            (reverse('posts:index'), HTTPStatus.OK),
            (reverse('posts:group_list',
             kwargs={'slug': PostUrlTest.group.slug}), HTTPStatus.OK),
            (reverse('posts:profile',
             kwargs={'username': PostUrlTest.user.username}), HTTPStatus.OK),
            (reverse('posts:post_detail',
             kwargs={'post_id': PostUrlTest.post.pk}), HTTPStatus.OK),
            (reverse('posts:post_edit',
             kwargs={'post_id': PostUrlTest.post.pk}), HTTPStatus.FOUND),
            (reverse('posts:post_create'), HTTPStatus.FOUND),
            (reverse('posts:follow_index'), HTTPStatus.FOUND),
            (reverse('posts:profile_unfollow',
             kwargs={'username': self.user.username}), HTTPStatus.FOUND)
        ]
        for url, status_code in url_status:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_response_authorized_client(self):
        """Статус страниц для зарегистрированого."""
        url_status = [
            (reverse('posts:index'), HTTPStatus.OK),
            (reverse('posts:group_list',
             kwargs={'slug': PostUrlTest.group.slug}), HTTPStatus.OK),
            (reverse('posts:profile',
             kwargs={'username': PostUrlTest.user.username}), HTTPStatus.OK),
            (reverse('posts:post_detail',
             kwargs={'post_id': PostUrlTest.post.pk}), HTTPStatus.OK),
            (reverse('posts:post_edit',
             kwargs={'post_id': PostUrlTest.post.pk}), HTTPStatus.OK),
            (reverse('posts:post_create'), HTTPStatus.OK),
        ]
        for url, status_code in url_status:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_404(self):
        """Cервер возвращает код 404, если страница не найдена."""
        response = self.guest_client.get('/notfound/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_template(self):
        """страница 404 отдаёт кастомный шаблон."""
        response = self.guest_client.get('/notfound/bla/bla/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template(self):
        """Проверяем запрашиваемые шаблоны страниц через имена."""
        templates_pages_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user.username}),
             'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
             'posts/post_detail.html'),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
             'posts/create_post.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse('posts:follow_index'), 'posts/follow.html'),
        ]
        for reverse_name, template in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
