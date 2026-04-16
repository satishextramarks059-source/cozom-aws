from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Apps
    path('', include('symptoms.urls')),
    path('user/', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),

    # Static Pages
    path('our-team/', TemplateView.as_view(template_name='our_team.html'), name='our_team'),
    path('testimonials/', TemplateView.as_view(template_name='testimonials.html'), name='testimonials'),
]

# ✅ MEDIA FILES (VERY IMPORTANT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)