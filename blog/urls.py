from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.BlogListView.as_view(), name='blog-list'),
    path('<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
    path('<slug:slug>/comment/', views.add_comment, name='add-comment'),
    path('comment/<uuid:comment_id>/edit/', views.edit_comment, name='edit-comment'),
    path('comment/<uuid:comment_id>/delete/', views.delete_comment, name='delete-comment'),
    path('<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    path('<slug:slug>/comments/load-more/', views.load_more_comments, name='load-more-comments'),
]