from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import MentorProfile, SelectedTalent, RejectedTalent

class HasSocialLinksFilter(admin.SimpleListFilter):
    title = 'Has Social Links'
    parameter_name = 'has_social_links'
    def lookups(self, request, model_admin):
        return (('yes', 'Yes'), ('no', 'No'))
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(social_links={})
        if self.value() == 'no':
            return queryset.filter(social_links={})
        return queryset

class SelectedTalentInline(admin.TabularInline):
    model = SelectedTalent
    extra = 0
    autocomplete_fields = ['talent']

class RejectedTalentInline(admin.TabularInline):
    model = RejectedTalent
    extra = 0
    autocomplete_fields = ['talent']

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = [
        'mentor_display',
        'coaching_experience_years',
        'is_verified',
        'is_featured',
        'is_available',
        'created_date',
        'display_social_links',
        'city',
        'state',
        'country',
    ]
    list_editable = ['is_verified', 'is_featured', 'is_available']
    list_filter = [
        'is_verified',
        'is_featured',
        'is_available',
        'coaching_style',
        'availability',
        'created_at',
        ('location', admin.EmptyFieldListFilter),
        HasSocialLinksFilter,
    ]
    search_fields = [
        'user__username',
        'user__email',
        'user__firstname',
        'user__lastname',
        'selected_sports',
        'location',
        'bio',
        'social_links',
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25
    actions = [
        'verify_mentors',
        'unverify_mentors',
        'feature_mentors',
        'unfeature_mentors',
        'export_mentor_data',
        'send_completion_reminder'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Basic Information', {
            'fields': ('bio', 'date_of_birth', 'location')
        }),
        ('Sports Coaching Information', {
            'fields': ('selected_sports', 'coaching_experience_years', 'playing_experience_years')
        }),
        ('Coaching Information', {
            'fields': ('coaching_style', 'max_students', 'coaching_levels')
        }),
        ('Media', {
            'fields': ('profile_picture',),
        }),
        ('Social Media', {
            'fields': ('social_links',),
        }),
        ('Availability', {
            'fields': ('availability', 'is_available')
        }),
        ('Profile Status', {
            'fields': ('is_verified', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [SelectedTalentInline, RejectedTalentInline]
    def mentor_display(self, obj):
        avatar_html = ""
        if obj.profile_picture:
            avatar_html = f'<img src="{obj.profile_picture.url}" width="40" height="40" style="border-radius: 50%; margin-right: 10px;" />'
        user_url = reverse('admin:userauths_user_change', args=[obj.user.id])
        profile_url = reverse('admin:mentor_mentorprofile_change', args=[obj.id])
        return format_html(
            '{}<a href="{}">{} {}</a><br><small style="color: #666;">Age: {} | <a href="{}">View Profile</a></small>',
            avatar_html,
            user_url,
            obj.user.get_full_name(),
            f"(@{obj.user.username})",
            obj.age if obj.age else "N/A",
            profile_url
        )
    mentor_display.short_description = "Mentor"
    mentor_display.admin_order_field = 'user__firstname'
    def display_social_links(self, obj):
        if not obj.social_links:
            return '-'
        icons = {
            "facebook": "🌐",
            "linkedin": "🔗",
            "instagram": "📸",
        }
        html = []
        for platform, url in obj.social_links.items():
            icon = icons.get(platform, platform.title())
            html.append(
                f'<a href="{url}" target="_blank" style="margin-right:8px;text-decoration:none;">{icon} {platform.title()}</a>'
            )
        return format_html(" | ".join(html))
    display_social_links.short_description = 'Social Links'

    def created_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y") if obj.created_at else "-"
    created_date.short_description = "Created"
    created_date.admin_order_field = 'created_at'

    # Custom actions
    def verify_mentors(self, request, queryset):
        """Verify selected mentors"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {count} mentors.")
    verify_mentors.short_description = "Verify selected mentors"
    
    def unverify_mentors(self, request, queryset):
        """Unverify selected mentors"""
        count = queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {count} mentors.")
    unverify_mentors.short_description = "Unverify selected mentors"
    
    def feature_mentors(self, request, queryset):
        """Feature selected mentors"""
        count = queryset.update(is_featured=True)
        self.message_user(request, f"Successfully featured {count} mentors.")
    feature_mentors.short_description = "Feature selected mentors"
    
    def unfeature_mentors(self, request, queryset):
        """Unfeature selected mentors"""
        count = queryset.update(is_featured=False)
        self.message_user(request, f"Successfully unfeatured {count} mentors.")
    unfeature_mentors.short_description = "Unfeature selected mentors"
    
    def export_mentor_data(self, request, queryset):
        """Export mentor data"""
        self.message_user(request, f"Export functionality for {queryset.count()} mentors would be implemented here.")
    export_mentor_data.short_description = "Export mentor data"
    
    def send_completion_reminder(self, request, queryset):
        """Send profile completion reminder"""
        self.message_user(request, "Profile completion reminder would be sent to mentors (feature removed).")
    send_completion_reminder.short_description = "Send completion reminder"
    
    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('user')

@admin.register(SelectedTalent)
class SelectedTalentAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'talent', 'selected_at']
    search_fields = ['mentor__user__username', 'talent__user__username']
    autocomplete_fields = ['mentor', 'talent']

@admin.register(RejectedTalent)
class RejectedTalentAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'talent', 'rejected_at']
    search_fields = ['mentor__user__username', 'talent__user__username']
    autocomplete_fields = ['mentor', 'talent']
