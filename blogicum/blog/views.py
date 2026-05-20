from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    DeleteView,
)
from .forms import ProfileForm, PostForm, CommentForm
from .models import Category, Post, Comment
from django.db.models import Count
from django.http import Http404


# only_published=True фильтрует посты по дате и статусу публикации,
# = False возвращает весь queryset
def get_posts_queryset(queryset=None, only_published=True):
    if queryset is None:
        queryset = Post.objects.all()

    queryset = queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    if only_published:
        queryset = queryset.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )

    return queryset


# Устранение дублирования dispatch
# Разрешает редактировать или удалять пост только автору.
class PostAuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return post.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


# Разрешает редактировать или удалять комментарий только автору.
class CommentAuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        comment = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        return comment.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


# CBV
class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        return get_posts_queryset(only_published=True)


class RegisterCreateView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        # Вместо создания нового запроса: self.category.posts
        return get_posts_queryset(
            self.category.posts.all(),
            only_published=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        # Защита от AnonymousUser
        current_user = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )

        try:
            # queryset выбираем в зависимости от того, автор смотрит или нет
            # Если автор - ищем по всему queryset
            # Если другой пользователь, то строго в опубликованных.
            # (без if)
            author_qs = get_posts_queryset(only_published=False).filter(
                author=current_user
            )
            return get_object_or_404(author_qs, pk=self.kwargs['post_id'])
        except Http404:
            return get_object_or_404(
                get_posts_queryset(only_published=True),
                pk=self.kwargs['post_id']
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, PostAuthorRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, PostAuthorRequiredMixin, DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {'instance': self.object}
        return context

    def get_success_url(self):
        return reverse('blog:index')


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.profile_user = get_object_or_404(
            User,
            username=self.kwargs['username']
        )

        user_posts = self.profile_user.posts.all()

        # Если страницу смотрит автор - отключаем фильтрацию по публикации
        is_owner = self.request.user == self.profile_user

        return get_posts_queryset(user_posts, only_published=not is_owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile_user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(
    LoginRequiredMixin, CommentAuthorRequiredMixin, UpdateView
):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentDeleteView(
    LoginRequiredMixin, CommentAuthorRequiredMixin, DeleteView
):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {'instance': self.object}
        return context

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )
