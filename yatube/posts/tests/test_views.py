import random
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.utils import COUNT_POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.new_user = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.form_fields = [
            ('group', forms.fields.ChoiceField),
            ('text', forms.fields.CharField),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTest.user)
        cache.clear()

    def _post_has_attributes(self, post_object):
        """приватный метод проверки контекста"""
        self.assertEqual(post_object.author, PostViewTest.user)
        self.assertEqual(post_object.text, PostViewTest.post.text)
        self.assertEqual(post_object.pub_date, PostViewTest.post.pub_date)
        self.assertEqual(post_object.image, PostViewTest.post.image)

    def test_index_page_show_correct_context(self):
        """Проверяем, что словарь context страницы /index
        в первом элементе списка page_obj содержит ожидаемые значения"""
        response = self.guest_client.get(reverse('posts:index'))
        post_object = response.context['page_obj'][0]
        self._post_has_attributes(post_object)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'].title,
                         PostViewTest.group.title)
        self.assertEqual(response.context['group'].description,
                         PostViewTest.group.description)
        self.assertEqual(response.context['group'].slug,
                         PostViewTest.group.slug)
        post_object = response.context['page_obj'][0]
        self._post_has_attributes(post_object)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': PostViewTest.user.username})
        )
        profile_auth = response.context['author']
        self.assertEqual(profile_auth.username, PostViewTest.user.username)
        post_object = response.context['page_obj'][0]
        self._post_has_attributes(post_object)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': PostViewTest.post.pk})
        )
        post_object = response.context['post']
        self.assertEqual(post_object.author.username,
                         PostViewTest.user.username)
        self.assertEqual(post_object.text,
                         PostViewTest.post.text)

    def test_edit_pages_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': PostViewTest.post.pk}))
        for value, expected in PostViewTest.form_fields:
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in PostViewTest.form_fields:
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        new_post = Post.objects.create(
            text='Пост при создании добавлен корректно',
            author=self.user,
            group=self.group)
        templates_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user.username}),
             'posts/profile.html'),
        ]
        for reverse_name, template in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(new_post, response.context['page_obj'])

    def test_post_added_correctly_another_user(self):
        """Пост при создании не добавляется другому пользователю"""
        posts_count = Post.objects.filter(group=self.new_group).count()
        Post.objects.create(
            text='Тестовый текст поста',
            author=self.user,
            group=self.group,
        )
        self.assertEqual(Post.objects.filter(
            group=self.new_group).count(), posts_count
        )
        self.assertNotEqual(Post.objects.filter(
            group=self.group).count(), posts_count
        )

    def test_cache_context(self):
        '''Проверка кэширования страницы index'''
        before_create_post = self.authorized_client.get(
            reverse('posts:index'))
        first_item_before = before_create_post.content
        Post.objects.create(
            author=self.user,
            text='Проверка кэша',
            group=self.group)
        after_create_post = self.authorized_client.get(reverse('posts:index'))
        first_item_after = after_create_post.content
        self.assertEqual(first_item_after, first_item_before)
        cache.clear()
        after_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_item_after, after_clear)


class PaginatorViewsTest(TestCase):
    """тестируем паджинатор"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_group')

        posts = []
        cls.first_page = COUNT_POSTS
        cls.second_page = random.randint(1, COUNT_POSTS)
        cls.all_posts = cls.first_page + cls.second_page
        for i in range(cls.all_posts):
            posts.append(Post(text=f'Тестовый текст {i}',
                              group=cls.group,
                              author=cls.user))
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        cache.clear()

    def test_first_page(self):
        templates_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user.username}),
             'posts/profile.html'),
        ]
        for reverse_name, template in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), self.first_page)

    def test_second_page(self):
        templates_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user.username}),
             'posts/profile.html'),
        ]
        for reverse_name, template in templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 self.second_page)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей.
        """
        count_follow = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': self.user2.username}))
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, self.user2)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """
        Авторизованный пользователь может удалять их из подписок.
        """
        count_follow = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': self.user2.username}))
        Follow.objects.create(user=self.user, author=self.user2)
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                   kwargs={'username': self.user2.username}))
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follower_see_new_post(self):
        '''Новая запись пользователя появляется в ленте тех,
         кто на него подписан'''
        new_post = Post.objects.create(
            author=FollowViewsTest.user2,
            text='Текстовый текст')
        Follow.objects.get_or_create(user=FollowViewsTest.user,
                                     author=FollowViewsTest.user2)
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_posts = response_follower.context['page_obj']
        self.assertIn(new_post, new_posts)

    def test_unfollower_no_see_new_post(self):
        '''Новая запись не появляется в ленте тех, кто не подписан.'''
        new_post = Post.objects.create(
            author=FollowViewsTest.user2,
            text='Текстовый текст')
        Follow.objects.get_or_create(user=FollowViewsTest.user,
                                     author=FollowViewsTest.user2)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_posts = response_unfollower.context['page_obj']
        self.assertNotIn(new_post, new_posts)
        self.assertEqual(len(new_posts), 0)
