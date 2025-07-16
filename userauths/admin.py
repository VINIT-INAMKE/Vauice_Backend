from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'user_display', 
        'user_type_badge', 
        'verification_status', 
        'last_login_status',
        'date_joined_formatted'
    ]
    list_filter = [
        'user_type', 
        'is_staff', 
        'is_active', 
        'gender', 
        'date_joined',
        ('last_login', admin.EmptyFieldListFilter),
    ]
    search_fields = [
        'username', 
        'email', 
        'firstname', 
        'lastname',
        'phone_number'
    ]
    ordering = ('-date_joined',)
    list_per_page = 25
    
    # Custom actions
    actions = [
        'activate_users', 
        'deactivate_users', 
        'verify_users', 
        'unverify_users',
        'export_user_data',
        'send_welcome_email'
    ]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('firstname', 'lastname', 'email', 'full_name', 'gender', 'age', 'phone_number')
        }),
        ('User Type & Status', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
        ('Avatar', {'fields': ('avatar',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'firstname', 'lastname', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def user_display(self, obj):
        """Display user with avatar and verification status"""
        avatar_html = ""
        if obj.avatar:
            avatar_html = f'<img src="{obj.avatar.url}" width="30" height="30" style="border-radius: 50%; margin-right: 10px;" />'
        
        # Remove verification icon since is_verified field doesn't exist
        user_url = reverse('admin:userauths_user_change', args=[obj.id])
        
        return mark_safe(
            f'{avatar_html}<a href="{user_url}">{obj.get_full_name()} (@{obj.username})</a><br><small style="color: #666;">{obj.email}</small>'
        )
    user_display.short_description = "User"
    user_display.admin_order_field = 'user__firstname'
    
    def user_type_badge(self, obj):
        """Display user type with color coding"""
        colors = {
            'talent': 'blue',
            'mentor': 'green', 
            'admin': 'red'
        }
        color = colors.get(obj.user_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_user_type_display().upper()
        )
    user_type_badge.short_description = "User Type"
    user_type_badge.admin_order_field = 'user_type'
    
    def verification_status(self, obj):
        """Display verification status - placeholder since is_verified field doesn't exist"""
        return format_html('<span style="color: gray;">N/A</span>')
    verification_status.short_description = "Verification"
    
    def last_login_status(self, obj):
        """Display last login status"""
        if obj.last_login:
            days_ago = (timezone.now() - obj.last_login).days
            if days_ago == 0:
                return format_html('<span style="color: green;">Today</span>')
            elif days_ago == 1:
                return format_html('<span style="color: orange;">Yesterday</span>')
            elif days_ago <= 7:
                return format_html('<span style="color: orange;">{} days ago</span>', days_ago)
            else:
                return format_html('<span style="color: red;">{} days ago</span>', days_ago)
        else:
            return format_html('<span style="color: gray;">Never</span>')
    last_login_status.short_description = "Last Login"
    last_login_status.admin_order_field = 'last_login'
    
    def date_joined_formatted(self, obj):
        """Display formatted join date"""
        return obj.date_joined.strftime("%b %d, %Y")
    date_joined_formatted.short_description = "Joined Date"
    date_joined_formatted.admin_order_field = 'date_joined'
    
    # Custom actions
    def activate_users(self, request, queryset):
        """Activate selected users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {count} users.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {count} users.")
    deactivate_users.short_description = "Deactivate selected users"
    
    def verify_users(self, request, queryset):
        """Verify selected users - placeholder since is_verified field doesn't exist"""
        self.message_user(request, "Verification functionality not available - is_verified field not implemented.")
    verify_users.short_description = "Verify selected users"
    
    def unverify_users(self, request, queryset):
        """Unverify selected users - placeholder since is_verified field doesn't exist"""
        self.message_user(request, "Unverification functionality not available - is_verified field not implemented.")
    unverify_users.short_description = "Unverify selected users"
    
    def export_user_data(self, request, queryset):
        """Export user data"""
        self.message_user(request, f"Export functionality for {queryset.count()} users would be implemented here.")
    export_user_data.short_description = "Export user data"
    
    def send_welcome_email(self, request, queryset):
        """Send welcome email to users"""
        self.message_user(request, f"Welcome email functionality for {queryset.count()} users would be implemented here.")
    send_welcome_email.short_description = "Send welcome email"
    
    def save_model(self, request, obj, form, change):
        # Set admin users as staff and superuser
        if obj.user_type == 'admin':
            obj.is_staff = True
            obj.is_superuser = True
        super().save_model(request, obj, form, change)
    
    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related(
            'talent_profile',
            'mentor_profile'
        )
