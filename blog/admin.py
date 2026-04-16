from django.contrib import admin
from .models import Blog, Comment, Like

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'created_at', 'likes_count', 'comments_count', 'is_deleted']
    list_filter = ['created_at', 'is_deleted']
    search_fields = ['title', 'tags', 'creator__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['likes_count', 'comments_count']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'blog', 'created_at', 'is_deleted']
    list_filter = ['created_at', 'is_deleted']
    search_fields = ['user__username', 'blog__title', 'content']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'blog', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'blog__title']