# unitribe_server/posts/urls.py - FIXED
from django.urls import path
from .views import (
    PostListCreateView, PostDetailView, LikePostView,
    UnlikePostView, CommentCreateView, CommentDeleteView, 
    UserFeedView
)

urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),
    path('feed/', UserFeedView.as_view(), name='user-feed'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:post_id>/like/', LikePostView.as_view(), name='like-post'),
    path('<int:post_id>/unlike/', UnlikePostView.as_view(), name='unlike-post'),
    path('<int:post_id>/comments/', CommentCreateView.as_view(), name='create-comment'),
    path('<int:post_id>/comments/<int:comment_id>/', CommentDeleteView.as_view(), name='delete-comment'),
]