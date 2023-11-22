from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250,
                            unique_for_date='publish')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='blog_posts')
    body = models.TextField()

    publish = models.DateTimeField(default=timezone.now)  # поле дата публикации
    created = models.DateTimeField(auto_now_add=True)  # поле дата создания
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)

    objects = models.Manager()  # менеджер, применяемый по умолчанию
    published = PublishedManager()
    tags = TaggableManager()

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def get_absolute_url(self):
        return reverse('blog:post_detail',
                       args=[self.publish.year,
                             self.publish.month,
                             self.publish.day,
                             self.slug])

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments')  # Пост объекта комментариев можно извлекать посредством comment.
    # post и все комментарии, ассоциированные с объектом-постом, – посредством post.comments.all()
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'

    # python manage.py shell
    # Выполните следующий ниже исходный код, чтобы получить один из постов (пост с ID = 1):
    #
    # from blog.models import Post
    # post = Post.objects.get(id=1)
    # Затем добавьте в него несколько тегов и извлеките его теги, чтобы проверить успешность их добавления:
    #
    # post.tags.add('music', 'jazz', 'django')
    #
    # post.tags.all()
    # <QuerySet [<Tag: jazz>, <Tag: music>, <Tag: django>]>
    # Наконец, удалите тег и еще раз проверьте список тегов:
    #
    # post.tags.remove('django')
    # post.tags.all()

# 1) Можно еще добавить в класс Meta verbose_name = 'комментарий' и verbose_name_plural = 'Комментарии' ,
# то же сделать и с моделью Post
#
# 2) В settings.py LANGUAGE_CODE = 'ru-RU'
#
# 3) В apps.py у класса BlogConfig установить verbose_name = 'Блог'

# python3 manage.py makemigrations blog
# python3 manage.py migrate

