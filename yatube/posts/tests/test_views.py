from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.second_group = Group.objects.create(
            title='Тестовый заголовок 2',
            slug='test-second_group-slug',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='NoNameUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostsViewsTests.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'SomeUser'}):
                'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': PostsViewsTests.post.id
                }
            ):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': PostsViewsTests.post.id}
            ):
                'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_index_page_show_correct_context(self):
        """Шаблон Index сформированf с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый текст')

    def test_pages_group_list_page_show_correct_context(self):
        """Шаблон group_list сформированf с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'})
        )
        first_object = response.context["group"]
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, 'Тестовый заголовок')
        self.assertEqual(group_slug_0, 'test-group-slug')

    def test_pages_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'SomeUser'}))
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username, 'SomeUser')
        self.assertEqual(post_text_0, 'Тестовый текст')

    def test_pages_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': PostsViewsTests.post.pk
                })
        )
        self.assertEqual(response.context.get('post').text, 'Тестовый текст')

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertTrue('is_edit' in response.context)

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_new_post_in_correct_pages(self):
        """Новый пост появляется на главной странице, на странице группы и
        в профайле пользователя"""
        exp_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': 'SomeUser'})
        ]
        for revers in exp_pages:
            with self.subTest(revers=revers):
                response = self.authorized_client.get(revers)
                self.assertIn(self.post, response.context['page_obj'])

    def test_new_post_not_in_wrong_group(self):
        """Пост не попал в группу, для которой не был предназначен"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.second_group.slug}
            )
        )
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        objs = [
            Post(
                author=cls.author,
                group=cls.group,
                text='Тестовый текст',
            )
            for bulk in range(1, 14)
        ]
        cls.post = Post.objects.bulk_create(objs)

    def test_first_page_pajination(self):
        """Проверка паджинации на странице index"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_pajination(self):
        """Проверка паджинации на второй странице index"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_pajination(self):
        """Проверка паджинации на странице group_list"""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_pajination(self):
        """Проверка паджинации на странице profile"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.author.username}))
        self.assertEqual(len(response.context['page_obj']), 10)
