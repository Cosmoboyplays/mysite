from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import EmptyPage, PageNotAnInteger
from taggit.models import Tag
from django.db.models import Count
from django.core.mail import send_mail
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from django.core.paginator import Paginator

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post

from django.db.models.functions import Lower
from django.contrib.postgres.search import TrigramSimilarity


def post_list(request, tag_slug=None):
    ppp = Post.objects.filter(title__search='Музыка')
    post_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        # Если page_number находится вне диапазона, то
        # выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        # Если page_number не целое число, то
        # выдать первую страницу
        posts = paginator.page(1)

    return render(request,
                  'blog/post/list.html',
                  {'posts': posts,
                   'tag': tag,
                   'ppp': ppp})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,  # мы указываем, что мы хотим получить объекты  Post ,
                             # у которых значение поля  status  равно  PUBLISHED
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    # Форма для комментирования пользователями
    form = CommentForm()
    # Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True)  # список идентификаторов тегов текущего поста
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)  # все опубликованные посты,
    # у которых есть теги, содержащиеся в списке  post_tags_ids , за исключением текущего поста
    similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
                        .order_by('-same_tags', '-publish')[:4]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   "comments": comments,
                   'form': form,
                   'similar_posts': similar_posts})


def post_share(request, post_id):
    # Извлечь пост по его идентификатору id
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s ({cd['email']}) comments: {cd['comments']}"
            send_mail(subject, message, 'halk53400@gmail.com',
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.post = post
        # Сохранить комментарий в базе данных
        comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post': post,
                   'form': form,
                   'comment': comment})

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B', config='simple')
            search_query = SearchQuery(query, config='simple')
            results = Post.published.annotate(rank=SearchRank(search_vector, search_query)
                                              ).filter(rank__gte=0.3).order_by('-rank')

    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})