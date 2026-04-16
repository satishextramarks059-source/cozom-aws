import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from PIL import Image



# Class-based image validator

class ValidateImageDimensions:
    def __init__(self, width=None, height=None):
        self.width = width
        self.height = height

    def __call__(self, image):
        if not image:
            return
        from PIL import Image
        from django.core.exceptions import ValidationError

        img = Image.open(image)
        if self.width and img.width != self.width:
            raise ValidationError(f"Image width must be {self.width}px.")
        if self.height and img.height != self.height:
            raise ValidationError(f"Image height must be {self.height}px.")

    # This makes Django migrations work
    def deconstruct(self):
        return (
            f"{self.__module__}.{self.__class__.__name__}",  # import path
            [],  # positional args
            {"width": self.width, "height": self.height},  # keyword args
        )




# Blog model

class Blog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    tags = models.CharField(max_length=500, help_text="Comma separated tags")

    # CKEditor content fields
    content_intro = CKEditor5Field(verbose_name="Introduction")
    content_section1 = CKEditor5Field(verbose_name="Section 1", blank=True)
    content_section2 = CKEditor5Field(verbose_name="Section 2", blank=True)
    content_conclusion = CKEditor5Field(verbose_name="Conclusion", blank=True)

    # Images with validation
    thumbnail = models.ImageField(
        upload_to="blog/thumbnails/",
        validators=[ValidateImageDimensions(800, 400)],
        help_text="Thumbnail image (800x400px)"
    )
    image1 = models.ImageField(
        upload_to="blog/images/",
        validators=[ValidateImageDimensions(1200, 600)],
        help_text="Additional image 1 (1200x600px)"
    )
    image2 = models.ImageField(
        upload_to="blog/images/",
        validators=[ValidateImageDimensions(1200, 600)],
        help_text="Additional image 2 (1200x600px)"
    )
    image3 = models.ImageField(
        upload_to="blog/images/",
        validators=[ValidateImageDimensions(1200, 600)],
        help_text="Additional image 3 (1200x600px)"
    )

    # Creator information
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creator_email = models.EmailField()
    creator_phone = models.CharField(max_length=15, blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_deleted", "created_at"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_detail", kwargs={"slug": self.slug})

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


#  Comment model
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.blog.title}"



#  Like model

class Like(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["blog", "user"]

    def __str__(self):
        return f"Like by {self.user.username} on {self.blog.title}"
