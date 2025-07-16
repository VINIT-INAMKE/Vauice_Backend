from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class TalentProfile(models.Model):
    """Profile model for Talent users"""
    
    # Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='talent_profile')
    bio = models.TextField(max_length=1000, blank=True, help_text="Tell us about yourself")
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Sports Information
    selected_sports = models.JSONField(default=list, blank=True, help_text="List of selected sports from the 25-30 sports list")
    experience_years = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Years of experience in sports"
    )

    # Media (Instagram-style)
    profile_picture = models.ImageField(upload_to='talent/profiles/', null=True, blank=True, default="defaults/default-avatar.png")
    cover_photo = models.ImageField(upload_to='talent/covers/', null=True, blank=True)
    
    # Instagram-style content
    
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Social Media Links
    social_links = models.JSONField(default=dict, blank=True, help_text="Links to social media profiles (Facebook, Instagram, etc.)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Talent Profile')
        verbose_name_plural = _('Talent Profiles')
        db_table = 'talent_profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Talent Profile"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    
    def save(self, *args, **kwargs):
        # Remove profile completion calculation
        super().save(*args, **kwargs)

class Post(models.Model):
    talent = models.ForeignKey('TalentProfile', on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video = models.FileField(upload_to='posts/videos/', null=True, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        db_table = 'talent_posts'

    def __str__(self):
        return f"Post by {self.talent.user.get_full_name()} at {self.created_at}"

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_posts')
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        verbose_name = _('Post Like')
        verbose_name_plural = _('Post Likes')
        db_table = 'talent_post_likes'

    def __str__(self):
        return f"{self.user.get_full_name()} liked post {self.post.id}"

class PostView(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewed_posts')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        verbose_name = _('Post View')
        verbose_name_plural = _('Post Views')
        db_table = 'talent_post_views'

    def __str__(self):
        return f"{self.user.get_full_name()} viewed post {self.post.id}"
