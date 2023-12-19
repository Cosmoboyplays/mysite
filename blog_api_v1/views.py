from rest_framework import generics
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination

from blog.models import Post
from .serializers import PostSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions
from .permissions import IsAuthorOrReadOnly


class PostList(generics.ListCreateAPIView):
    permission_classes = (IsAuthorOrReadOnly,)  # new
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    # pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author']
    search_fields = ['body', 'author__username']
    # ordering_fields = ['author_id', 'publish']
    ordering_fields = '__all__'
    ordering = ['author']
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        # user = self.request.user
        # return Post.objects.filter(author=user)
        return Post.objects.all()


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthorOrReadOnly,)  # new
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    # permission_classes = (permissions.IsAdminUser,) # так только админы видят детальную инфу


class UserPostList(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.kwargs['username']
        return Post.objects.filter(author=user)