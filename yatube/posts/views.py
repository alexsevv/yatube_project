from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from . utils import use_paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().select_related('group', 'author')
    context = {
        'page_obj': use_paginator(request, post_list),
    }

    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all().select_related('author').order_by(
        '-pub_date')
    context = {
        'group': group,
        'page_obj': use_paginator(request, post_list),
    }

    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all().select_related('group')
    following = (request.user.is_authenticated
                 and Follow.objects.filter(
                     user=request.user,
                     author=author).exists())
    context = {
        "page_obj": use_paginator(request, post_list),
        "author": author,
        "following": following,
    }

    template = "posts/profile.html"
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    context = {
        "post": post,
        "author": author,
        'comments': comments,
        'form': form,
    }
    template = "posts/post_detail.html"
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect(
            'posts:profile', temp_form.author
        )

    template = 'posts/create_post.html'
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(
            'posts:post_detail', post_id
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            'posts:post_detail', post_id
        )
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }

    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts_list = Post.objects.filter(author__following__user=request.user)
    template = 'posts/follow.html'
    title = 'Публикации избранных авторов'
    context = {
        'title': title,
        "page_obj": use_paginator(request, posts_list),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    follow_author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(user=user, author=follow_author).delete()
    return redirect("posts:profile", username=username)
