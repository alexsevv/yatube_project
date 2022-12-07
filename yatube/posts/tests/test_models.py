from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, TEXT_LENGHT

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """правильно ли отображается значение поля __str__"""
        post = PostModelTest.post
        self.assertEqual(str(post), post.text[:TEXT_LENGHT])

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = [
            ('text', 'Текст поста'),
            ('pub_date', 'Дата публикации'),
            ('author', 'Автор'),
            ('group', 'Группа'),
        ]
        for value, expected in field_verboses:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = [
            ('text', 'Введите текст поста'),
            ('pub_date', 'Дата публикации поста'),
            ('author', 'Автор поста'),
            ('group', 'Группа, к которой будет относиться пост'),
        ]
        for value, expected in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа 2',
            slug='grupa2',
            description='тестовое описание группы'
        )

    def test_models_have_correct_object_names(self):
        """правильно ли отображается значение поля __str__"""
        group = GroupModelTest.group
        self.assertEqual(str(group), group.title)
