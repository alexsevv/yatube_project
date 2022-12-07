import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment
from posts.forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """при отправке валидной формы со страницы создания поста
        создаётся новая запись в базе данных"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            post.group, PostFormTests.group
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)

    def test_can_edit_post1(self):
        """при отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных"""
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group)
        self.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Описание')
        form_data = {
            'text': 'Текст записанный в форму', 'group': self.group2.pk}
        response = self.authorized_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
            id=self.post.pk,
            group=self.group2.pk,
            author=self.user,
            pub_date=self.post.pub_date
        ).exists())


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group',
                                         description='Описание')
        cls.post = Post.objects.create(text='Тестовый текст',
                                       author=cls.user,
                                       group=cls.group)
        cls.comment = Comment.objects.create(post_id=cls.post.pk,
                                             author=cls.user,
                                             text='первый тестовый коммент')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_no_edit_comment_guest(self):
        '''комментировать посты может только авторизованный пользователь'''
        posts_count = Comment.objects.count()
        form_data = {'text': 'второй тестовый коммент'}
        response = self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Comment.objects.count(),
                            posts_count + 1)
        self.assertNotEqual(self.comment.text, form_data['text'])

    def test_create_comment(self):
        '''после успешной отправки комментарий появляется на странице поста.'''
        comment_count = Comment.objects.count()
        form_data = {'text': 'второй тестовый коммент'}
        response = self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        new_comment = Comment.objects.last()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.post, CommentFormTest.post)
        self.assertEqual(new_comment.author, CommentFormTest.user)
