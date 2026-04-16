import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Blog, Comment, Like
from .forms import CommentForm, BlogSearchForm
from accounts.models import CustomUser
from collections import Counter
from django.db.models import Count, F, Value
from django.db.models.functions import Coalesce


class BlogListView(ListView):
    """
    Displays a paginated list of active blog posts with search and sorting options.
    Supports filtering blogs by title or tags and ordering by newest or oldest.
    Adds additional context including search form, popular blogs, popular tags, 
    and blog statistics (total blogs, comments, likes, and active writers).
    """
    model = Blog
    template_name = 'blog/blog_list.html'
    context_object_name = 'blogs'
    paginate_by = 4
    
    def get_queryset(self):
        queryset = Blog.objects.filter(is_deleted=False)
        
        # Search functionality
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(tags__icontains=query) | 
                Q(title__icontains=query)
            )
        
        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            queryset = queryset.order_by('created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = BlogSearchForm(self.request.GET)
        
        context['popular_blogs'] = (
            Blog.objects.filter(is_deleted=False)
            .annotate(
                total_popularity=Coalesce(F('likes_count'), Value(0)) + Coalesce(F('comments_count'), Value(0))
            )
            .order_by('-total_popularity', '-created_at')[:5]
        )
        
        # Get popular tags from all blogs
        all_tags = []
        for blog in Blog.objects.filter(is_deleted=False):
            all_tags.extend(blog.get_tags_list())
        
        tag_counts = Counter(all_tags)
        context['popular_tags'] = [tag for tag, count in tag_counts.most_common(10)]
        
        # Stats data
        context['total_blogs'] = Blog.objects.filter(is_deleted=False).count()
        context['total_comments'] = Comment.objects.filter(is_deleted=False).count()
        context['total_likes'] = Like.objects.count()
        context['active_writers'] = CustomUser.objects.filter(
            blog__isnull=False
        ).distinct().count()
        
        return context

class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'
    context_object_name = 'blog'
    
    def get_queryset(self):
        return Blog.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blog = self.object
        
        # Get first 5 comments
        comments = blog.comments.filter(is_deleted=False)[:5]
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        context['total_comments'] = blog.comments.filter(is_deleted=False).count()
        context['user_has_liked'] = False
        context['user_comment'] = None
        
        if self.request.user.is_authenticated:
            context['user_has_liked'] = Like.objects.filter(
                blog=blog, user=self.request.user
            ).exists()
            context['user_comment'] = blog.comments.filter(
                user=self.request.user, is_deleted=False
            ).first()
            
        return context

@login_required
@require_http_methods(["POST"])
def add_comment(request, slug):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        blog = get_object_or_404(Blog, slug=slug, is_deleted=False)
        
        # Check if user already commented
        existing_comment = Comment.objects.filter(
            blog=blog, user=request.user, is_deleted=False
        ).first()
        
        if existing_comment:
            return JsonResponse({
                'success': False,
                'message': 'You have already commented on this blog.'
            }, status=400)
        
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
            
            # Update comments count
            blog.comments_count = blog.comments.filter(is_deleted=False).count()
            blog.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Comment added successfully.',
                'comment': {
                    'id': str(comment.id),
                    'content': comment.content,
                    'user_name': comment.user.username,
                    'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'can_edit': True
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data.',
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

@login_required
@require_http_methods(["POST"])
def edit_comment(request, comment_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Comment updated successfully.',
                'content': comment.content
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data.',
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_comment(request, comment_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        blog = comment.blog
        comment.is_deleted = True
        comment.save()
        
        # Update comments count
        blog.comments_count = blog.comments.filter(is_deleted=False).count()
        blog.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Comment deleted successfully.'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

@login_required
@require_http_methods(["POST"])
def toggle_like(request, slug):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        blog = get_object_or_404(Blog, slug=slug, is_deleted=False)
        
        like, created = Like.objects.get_or_create(blog=blog, user=request.user)
        
        if not created:
            # Unlike
            like.delete()
            liked = False
        else:
            liked = True
        
        # Update likes count
        blog.likes_count = blog.likes.count()
        blog.save()
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': blog.likes_count
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

def load_more_comments(request, slug):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        blog = get_object_or_404(Blog, slug=slug, is_deleted=False)
        offset = int(request.GET.get('offset', 0))
        limit = 5
        
        comments = blog.comments.filter(is_deleted=False)[offset:offset + limit]
        
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': str(comment.id),
                'content': comment.content,
                'user_name': comment.user.username,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'can_edit': request.user.is_authenticated and comment.user == request.user
            })
        
        has_more = blog.comments.filter(is_deleted=False).count() > offset + limit
        
        return JsonResponse({
            'success': True,
            'comments': comments_data,
            'has_more': has_more,
            'new_offset': offset + len(comments_data)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)