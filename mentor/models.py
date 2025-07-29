from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from talent.models import TalentProfile

class SelectedTalent(models.Model):
    mentor = models.ForeignKey('MentorProfile', on_delete=models.CASCADE, related_name='selected_talent_links')
    talent = models.ForeignKey(TalentProfile, on_delete=models.CASCADE, related_name='selected_by_mentor_links')
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mentor', 'talent')
        verbose_name = _('Selected Talent')
        verbose_name_plural = _('Selected Talents')
        db_table = 'selected_talents'

    def __str__(self):
        return f"{self.mentor.user.get_full_name()} selected {self.talent.user.get_full_name()}"

class RejectedTalent(models.Model):
    mentor = models.ForeignKey('MentorProfile', on_delete=models.CASCADE, related_name='rejected_talent_links')
    talent = models.ForeignKey(TalentProfile, on_delete=models.CASCADE, related_name='rejected_by_mentor_links')
    rejected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mentor', 'talent')
        verbose_name = _('Rejected Talent')
        verbose_name_plural = _('Rejected Talents')
        db_table = 'rejected_talents'

    def __str__(self):
        return f"{self.mentor.user.get_full_name()} rejected {self.talent.user.get_full_name()}"

class MentorProfile(models.Model):
    """Profile model for Mentor users"""
    
    # Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    bio = models.TextField(max_length=1000, blank=True, help_text="Tell us about yourself")
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Sports Coaching Information
    selected_sports = models.JSONField(default=list, blank=True, help_text="List of selected sports from the 25-30 sports list")
    coaching_experience_years = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Years of coaching experience"
    )
    playing_experience_years = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Years of playing experience"
    )
    COACHING_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('professional', 'Professional'),
    ]
    coaching_levels = models.CharField(
        max_length=20,
        choices=COACHING_LEVEL_CHOICES,
        default='beginner',
        help_text="Coaching level (Beginner, Intermediate, Advanced, Professional)"
    )
    
    # Social Media Links
    social_links = models.JSONField(default=dict, blank=True, help_text="Links to social media profiles (Facebook, Instagram, etc.)")
    
    # Coaching Information
    coaching_style = models.CharField(
        max_length=20,
        choices=[
            ('structured', 'Structured Training'),
            ('flexible', 'Flexible Approach'),
            ('hands_on', 'Hands-on Coaching'),
            ('video_analysis', 'Video Analysis'),
            ('performance_based', 'Performance-Based'),
            ('mixed', 'Mixed Approach'),
        ],
        default='mixed'
    )
    max_students = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum number of students per session"
    )
    
    # Media
    profile_picture = models.ImageField(upload_to='mentor/profiles/', null=True, blank=True, default="defaults/default-avatar.png")
    
    # Availability
    availability = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('seasonal', 'Seasonal'),
            ('weekends', 'Weekends Only'),
            ('evenings', 'Evenings Only'),
            ('flexible', 'Flexible'),
        ],
        default='flexible'
    )
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    selected_talents = models.ManyToManyField(
        TalentProfile,
        through='SelectedTalent',
        related_name='mentors_selected'
    )
    rejected_talents = models.ManyToManyField(
        TalentProfile,
        through='RejectedTalent',
        related_name='mentors_rejected'
    )
    
    class Meta:
        verbose_name = _('Mentor Profile')
        verbose_name_plural = _('Mentor Profiles')
        db_table = 'mentor_profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Mentor Profile"
    
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
        super().save(*args, **kwargs)
