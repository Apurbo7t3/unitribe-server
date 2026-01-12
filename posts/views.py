# unitribe_server/posts/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Post, Comment
from .serializers import PostSerializer, PostCreateSerializer, CommentSerializer
from users.models import User  # Add this import
from notifications.models import Notification  # Add notifications for likes/comments
from users.models import User  # Add this line

class PostListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = Post.objects.all()
        
        # Filter by type
        post_type = self.request.query_params.get('type')
        if post_type:
            queryset = queryset.filter(post_type=post_type)
        
        # Filter by club
        club_id = self.request.query_params.get('club')
        if club_id:
            queryset = queryset.filter(club_id=club_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        
        # Order by latest
        queryset = queryset.order_by('-created_at')
        
        return queryset

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        
        # Create notification for club members if post belongs to a club
        if post.club:
            for member in post.club.members.all():
                if member != self.request.user:
                    Notification.objects.create(
                        user=member,
                        notification_type='post',
                        title=f'New Post in {post.club.name}',
                        message=f'{self.request.user.get_full_name()} posted: {post.title}',
                        related_id=post.id
                    )

class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class LikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        post.likes.add(request.user)
        return Response({'status': 'liked', 'like_count': post.like_count})

class UnlikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        post.likes.remove(request.user)
        return Response({'status': 'unliked', 'like_count': post.like_count})

class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['post'] = get_object_or_404(Post, id=self.kwargs['post_id'])
        context['author'] = self.request.user
        return context
    
    def perform_create(self, serializer):
        serializer.save()

class CommentDeleteView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        # Check if user is author or post author
        if comment.author != self.request.user and comment.post.author != self.request.user:
            self.permission_denied(self.request)
        return comment

class UserFeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        # Return ALL posts ordered by latest
        return Post.objects.all().order_by('-created_at')
    

