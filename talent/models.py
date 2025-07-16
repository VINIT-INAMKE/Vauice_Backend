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
    primary_sport = models.CharField(max_length=100, blank=True, help_text="Primary sport (e.g., Football, Basketball, Tennis)")
    experience_years = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Years of experience in sports"
    )
    achievements = models.JSONField(default=list, blank=True, help_text="List of sports achievements and awards")
    certifications = models.JSONField(default=list, blank=True, help_text="List of sports certifications and licenses")
    
    # Profile Status
    # Remove is_profile_complete and profile_completion_percentage
    

    
    # Media (Instagram-style)
    profile_picture = models.ImageField(upload_to='talent/profiles/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='talent/covers/', null=True, blank=True)
    
    # Instagram-style content
    profile_videos = models.JSONField(default=list, blank=True, help_text="List of profile video URLs")
    highlight_reels = models.JSONField(default=list, blank=True, help_text="List of highlight reel URLs")
    

    
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
    
    def calculate_profile_completion(self):
        # Remove this method entirely
        pass
    
    def save(self, *args, **kwargs):
        # Remove profile completion calculation
        super().save(*args, **kwargs)


class TalentPortfolio(models.Model):
    """Portfolio items for Talent users - Sports achievements and highlights"""
    
    talent = models.ForeignKey(TalentProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200, help_text="Achievement or highlight title")
    description = models.TextField(help_text="Description of the achievement or highlight")
    sport = models.CharField(max_length=100, blank=True, help_text="Sport for this achievement")
    achievement_type = models.CharField(
        max_length=50,
        choices=[
            ('tournament', 'Tournament Win'),
            ('championship', 'Championship'),
            ('record', 'Record/Personal Best'),
            ('award', 'Award/Recognition'),
            ('performance', 'Outstanding Performance'),
            ('other', 'Other'),
        ],
        default='other'
    )
    image = models.ImageField(upload_to='talent/portfolio/', null=True, blank=True)
    video_url = models.URLField(blank=True, help_text="Video highlight URL")
    date_achieved = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Location of achievement")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Talent Portfolio')
        verbose_name_plural = _('Talent Portfolios')
        db_table = 'talent_portfolios'
    
    def __str__(self):
        return f"{self.talent.user.get_full_name()} - {self.title}"
