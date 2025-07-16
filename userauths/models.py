from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import RegexValidator
from .utils import get_avatar_url, validate_avatar_file



class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    USER_TYPE_CHOICES = [
        ('talent', 'Talent'),
        ('admin', 'Admin'),
        ('mentor', 'Mentor'),
    ]
    
    # Basic fields
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    
    # Contact fields
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    
    # Authentication fields
    otp = models.CharField(max_length=100, null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    
    # Avatar field
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Onboarding status
    onboarding_done = models.BooleanField(default=False, help_text="Has the user completed onboarding?")
    
    # Override username to be unique
    username = models.CharField(max_length=100, unique=True)
    
    # Full name field for compatibility
    full_name = models.CharField(max_length=100, null=True, blank=True)
    
    # Email as username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'firstname', 'lastname']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        if self.full_name:
            return self.full_name
        return f"{self.firstname} {self.lastname}"
    
    def get_short_name(self):
        return self.firstname
    
    @property
    def is_talent(self):
        return self.user_type == 'talent'
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_mentor(self):
        return self.user_type == 'mentor'
    
    def get_avatar_url(self):
        """Get avatar URL or default avatar"""
        return get_avatar_url(self)
    
    def save(self, *args, **kwargs):
        # Auto-generate username from email if not provided
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        
        # Auto-generate full_name if not provided
        if not self.full_name:
            self.full_name = f"{self.firstname} {self.lastname}"
        
        # Set admin users as staff by default
        if self.user_type == 'admin':
            self.is_staff = True
            self.is_superuser = True
        
        super(User, self).save(*args, **kwargs)
