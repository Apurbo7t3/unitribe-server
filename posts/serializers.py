# unitribe_server/posts/serializers.py

from rest_framework import serializers
from .models import Post, Comment
from users.serializers import UserBasicSerializer
from clubs.serializers import ClubSerializer

class CommentSerializer(serializers.ModelSerializer):
    author_details = UserBasicSerializer(source='author', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'updated_at', 'author_details']
        read_only_fields = ['id', 'author', 'post', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Get post and author from context
        post = self.context['post']
        author = self.context['author']
        
        # Create comment with post and author
        comment = Comment.objects.create(
            post=post,
            author=author,
            content=validated_data['content']
        )
        return comment

class PostSerializer(serializers.ModelSerializer):
    author_details = UserBasicSerializer(source='author', read_only=True)
    club_details = ClubSerializer(source='club', read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'likes')
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('title', 'content', 'post_type', 'club', 'file')



