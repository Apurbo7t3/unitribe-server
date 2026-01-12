# unitribe_server/posts/models.py

from django.db import models
from users.models import User
from clubs.models import Club

class Post(models.Model):
    POST_TYPES = [
        ('announcement', 'Announcement'),
        ('blog', 'Blog'),
        ('resource', 'Resource'),
        ('question', 'Question'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='general')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    file = models.FileField(upload_to='post_files/', blank=True, null=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def like_count(self):
        return self.likes.count()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.post}"
    
