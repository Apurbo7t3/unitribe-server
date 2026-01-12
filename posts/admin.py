from django.contrib import admin
from .models import Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_type', 'author', 'club', 'like_count', 'created_at')
    list_filter = ('post_type', 'club')
    search_fields = ('title', 'content', 'author__email', 'club__name')
    readonly_fields = ('like_count', 'created_at', 'updated_at')
    filter_horizontal = ('likes',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    search_fields = ('author__email', 'post__title', 'content')
    readonly_fields = ('created_at', 'updated_at')
