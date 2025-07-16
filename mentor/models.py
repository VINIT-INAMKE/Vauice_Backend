from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class MentorProfile(models.Model):
    """Profile model for Mentor users"""
    
    # Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    bio = models.TextField(max_length=1000, blank=True, help_text="Tell us about yourself")
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Sports Coaching Information
    selected_sports = models.JSONField(default=list, blank=True, help_text="List of selected sports from the 25-30 sports list")
    primary_sport = models.CharField(max_length=100, blank=True, help_text="Primary sport coached (e.g., Football, Basketball, Tennis)")
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
    expertise_areas = models.JSONField(default=list, blank=True, help_text="Coaching expertise areas (Technique, Fitness, Strategy, Mental Game, etc.)")
    certifications = models.JSONField(default=list, blank=True, help_text="List of coaching certifications and licenses")
    education = models.JSONField(default=list, blank=True, help_text="Educational background and sports qualifications")
    
    # Social Media Links
    social_links = models.JSONField(default=dict, blank=True, help_text="Links to social media profiles (Facebook, Instagram, etc.)")
    
    # Profile Status
    is_profile_complete = models.BooleanField(default=False, help_text="Profile completion status")
    
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
    coaching_levels = models.JSONField(default=list, blank=True, help_text="Coaching levels (Beginner, Intermediate, Advanced, Professional)")
    training_focus = models.JSONField(default=list, blank=True, help_text="Training focus areas (Technique, Fitness, Strategy, Mental Game, Recovery)")
    

    
    # Media
    profile_picture = models.ImageField(upload_to='mentor/profiles/', null=True, blank=True)
    

    
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
    
    def calculate_profile_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            'bio', 'location', 'primary_sport', 'coaching_experience_years',
            'profile_picture', 'selected_sports'
        ]
        
        completed_fields = 0
        for field in fields:
            value = getattr(self, field)
            if value and (isinstance(value, str) and value.strip() or 
                         isinstance(value, list) and len(value) > 0 or
                         isinstance(value, int) and value > 0 or
                         isinstance(value, float) and value > 0):
                completed_fields += 1
        
        percentage = int((completed_fields / len(fields)) * 100)
        self.profile_completion_percentage = percentage
        self.is_profile_complete = percentage >= 80
        return percentage
    
    def save(self, *args, **kwargs):
        # Calculate profile completion before saving
        self.calculate_profile_completion()
        super().save(*args, **kwargs)


class MentorPortfolio(models.Model):
    """Portfolio items for Mentor users - Coaching achievements and success stories"""
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200, help_text="Coaching achievement or success story title")
    description = models.TextField(help_text="Description of the coaching achievement or success story")
    sport = models.CharField(max_length=100, blank=True, help_text="Sport for this achievement")
    achievement_type = models.CharField(
        max_length=50,
        choices=[
            ('student_success', 'Student Success'),
            ('team_achievement', 'Team Achievement'),
            ('coaching_award', 'Coaching Award'),
            ('certification', 'Certification'),
            ('publication', 'Publication/Article'),
            ('other', 'Other'),
        ],
        default='other'
    )
    image = models.ImageField(upload_to='mentor/portfolio/', null=True, blank=True)
    video_url = models.URLField(blank=True, help_text="Video demonstration or testimonial URL")
    date_achieved = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Location of achievement")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Mentor Portfolio')
        verbose_name_plural = _('Mentor Portfolios')
        db_table = 'mentor_portfolios'
    
    def __str__(self):
        return f"{self.mentor.user.get_full_name()} - {self.title}"
