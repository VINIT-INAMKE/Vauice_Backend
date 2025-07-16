from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import TalentProfile, TalentPortfolio

class HasProfilePictureFilter(admin.SimpleListFilter):
    title = 'Has Profile Picture'
    parameter_name = 'has_profile_picture'
    def lookups(self, request, model_admin):
        return (('yes', 'Yes'), ('no', 'No'))
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(profile_picture='')
        if self.value() == 'no':
            return queryset.filter(profile_picture='')
        return queryset

class TalentPortfolioInline(admin.StackedInline):
    model = TalentPortfolio
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'sport', 'achievement_type', 'image', 'video_url', 'date_achieved', 'location', 'created_at', 'updated_at')
        }),
    )

@admin.register(TalentProfile)
class TalentProfileAdmin(admin.ModelAdmin):
    inlines = [TalentPortfolioInline]
    list_display = [
        'talent_display',
        'primary_sport',
        'experience_years',
        'is_verified',
        'is_featured',
        'created_date',
        'display_social_links',
    ]
    list_editable = ['is_verified', 'is_featured']
    list_filter = [
        'is_verified',
        'is_featured',
        'primary_sport',
        'experience_years',
        'created_at',
        ('location', admin.EmptyFieldListFilter),
        HasProfilePictureFilter,
    ]
    search_fields = [
        'user__username',
        'user__email',
        'user__firstname',
        'user__lastname',
        'primary_sport',
        'selected_sports',
        'location',
        'bio',
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25
    actions = [
        'verify_talents',
        'unverify_talents',
        'feature_talents',
        'unfeature_talents',
        'export_talent_data',
        'send_completion_reminder'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Basic Information', {
            'fields': ('bio', 'date_of_birth', 'location')
        }),
        ('Sports Information', {
            'fields': ('selected_sports', 'primary_sport', 'experience_years', 'achievements', 'certifications')
        }),
        ('Media Content', {
            'fields': ('profile_picture', 'cover_photo', 'profile_videos', 'highlight_reels'),
            'description': 'Instagram-style media content'
        }),
        ('Social Media', {
            'fields': ('social_links',),
        }),
        ('Profile Status', {
            'fields': ('is_verified', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    def talent_display(self, obj):
        avatar_html = ""
        if obj.profile_picture:
            avatar_html = f'<img src="{obj.profile_picture.url}" width="40" height="40" style="border-radius: 50%; margin-right: 10px;" />'
        user_url = reverse('admin:userauths_user_change', args=[obj.user.id])
        profile_url = reverse('admin:talent_talentprofile_change', args=[obj.id])
        return format_html(
            '{}<a href="{}">{} {}</a><br><small style="color: #666;">Age: {} | <a href="{}">View Profile</a></small>',
            avatar_html,
            user_url,
            obj.user.get_full_name(),
            f"(@{obj.user.username})",
            obj.age if obj.age else "N/A",
            profile_url
        )
    talent_display.short_description = "Talent"
    talent_display.admin_order_field = 'user__firstname'

    def sports_info(self, obj):
        """Display sports information"""
        sports = obj.selected_sports
        if sports:
            primary = obj.primary_sport or sports[0]
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                primary,
                f"{len(sports)} sports, {obj.experience_years} years exp"
            )
        return "No sports selected"
    sports_info.short_description = "Sports"
    sports_info.admin_order_field = 'primary_sport'

    def location_status(self, obj):
        """Display location with status"""
        if obj.location:
            return format_html(
                '<span style="color: green;">📍 {}</span>',
                obj.location
            )
        else:
            return format_html('<span style="color: red;">❌ No location</span>')
    location_status.short_description = "Location"
    location_status.admin_order_field = 'location'

    def verification_status(self, obj):
        """Display verification status"""
        if obj.is_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Verified</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">❌ Not Verified</span>'
            )
    verification_status.short_description = "Verification"
    verification_status.admin_order_field = 'is_verified'

    def media_status(self, obj):
        """Display media content status"""
        media_count = 0
        if obj.profile_picture:
            media_count += 1
        if obj.cover_photo:
            media_count += 1
        if obj.profile_videos:
            media_count += len(obj.profile_videos)
        if obj.highlight_reels:
            media_count += len(obj.highlight_reels)

        if media_count >= 3:
            color = "green"
            icon = "✅"
        elif media_count >= 1:
            color = "orange"
            icon = "⚠️"
        else:
            color = "red"
            icon = "❌"

        return format_html(
            '<span style="color: {};">{} {} items</span>',
            color, icon, media_count
        )
    media_status.short_description = "Media Content"

    def created_date(self, obj):
        """Display formatted creation date"""
        return obj.created_at.strftime("%b %d, %Y")
    created_date.short_description = "Created"
    created_date.admin_order_field = 'created_at'

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

    # Custom actions
    def verify_talents(self, request, queryset):
        """Verify selected talents"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {count} talents.")
    verify_talents.short_description = "Verify selected talents"

    def unverify_talents(self, request, queryset):
        """Unverify selected talents"""
        count = queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {count} talents.")
    unverify_talents.short_description = "Unverify selected talents"

    def feature_talents(self, request, queryset):
        """Feature selected talents"""
        count = queryset.update(is_featured=True)
        self.message_user(request, f"Successfully featured {count} talents.")
    feature_talents.short_description = "Feature selected talents"

    def unfeature_talents(self, request, queryset):
        """Unfeature selected talents"""
        count = queryset.update(is_featured=False)
        self.message_user(request, f"Successfully unfeatured {count} talents.")
    unfeature_talents.short_description = "Unfeature selected talents"

    def export_talent_data(self, request, queryset):
        """Export talent data"""
        self.message_user(request, f"Export functionality for {queryset.count()} talents would be implemented here.")
    export_talent_data.short_description = "Export talent data"

    def send_completion_reminder(self, request, queryset):
        """Send profile completion reminder"""
        incomplete_talents = queryset.filter(is_profile_complete=False)
        self.message_user(request, f"Profile completion reminder would be sent to {incomplete_talents.count()} talents.")
    send_completion_reminder.short_description = "Send completion reminder"

    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('user')
