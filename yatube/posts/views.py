from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from .models import Post, Group, User
from .forms import PostForm
from django.conf import settings
from django.contrib.auth.decorators import login_required


def index(request):
    title = "Главная страница проекта Yatube"
    posts = Post.objects.select_related('group')[:settings.COUNT_POSTS]
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': posts,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


@login_required
def group_posts(request, slug):
    title = "Все записи группы"
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:settings.COUNT_POSTS]
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def profile(request, username):
    title = "Профайл пользователя " + username
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user.id)
    posts_count = posts.count()
    paginator = Paginator(posts, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': user,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'title': title,
        'posts': posts,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_list = Post.objects.all()
    title = f'Пост {post.text[:30]}'
    context = {
        'post': post,
        'post_list': post_list,
        'title': title,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    else:
        form = PostForm()
        context = {
            'form': form,
        }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/create_post.html', context)