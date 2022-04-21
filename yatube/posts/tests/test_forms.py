from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post


User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug="test-group-slug",
            description="Тестовое описание"

        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_author = User.objects.create_user(username='NoNameUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_create_post(self):
        """Тест формы создания поста"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст',
                     'group': self.group.id}
        response = self.authorized_client.post(reverse(
            'posts:post_create'), data=form_data, follow=True
        )
        error1 = 'В посте ошибка'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
                        text='Тестовый текст',
                        group=1,
                        author=self.user
                        ).exists(), error1)
        error2 = 'Новая запись в базу данных не создана'
        self.assertEqual(Post.objects.count(),
                         posts_count + 1,
                         error2)

    def test_edit_post(self):
        """Проверка редактирования поста."""
        user_editor = User.objects.create(
            username='editor_not_owner_post'
        )
        authorized_editor = Client()
        authorized_editor.force_login(user_editor)

        form_data = {
            'text': 'Тестовый текст',
        }
        response = authorized_editor.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True
        )
        post = Post.objects.get()
        self.assertEqual(post.text, self.post.text)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.id])
        )
