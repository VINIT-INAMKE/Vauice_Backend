from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import TalentProfile, Post, PostLike, PostView

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

@admin.register(TalentProfile)
class TalentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'talent_display',
        'experience_years',
        'is_verified',
        'is_featured',
        'created_date',
        'display_social_links',
        'city',
        'state',
        'country',
    ]
    list_editable = ['is_verified', 'is_featured']
    list_filter = [
        'is_verified',
        'is_featured',
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
            'fields': ('bio', 'date_of_birth', 'location', 'city', 'state', 'country')
        }),
        ('Sports Information', {
            'fields': ('selected_sports', 'experience_years')
        }),
        ('Media Content', {
            'fields': ('profile_picture', 'cover_photo'),
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
        self.message_user(request, "Profile completion reminder would be sent to talents (feature removed).")
    send_completion_reminder.short_description = "Send completion reminder"

    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('user')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'post_display',
        'talent_display',
        'content_preview',
        'has_media',
        'likes_count',
        'views_count',
        'created_date',
    ]
    list_filter = [
        'created_at',
        'updated_at',
        ('content', admin.EmptyFieldListFilter),
        ('image', admin.EmptyFieldListFilter),
        ('video', admin.EmptyFieldListFilter),
    ]
    search_fields = [
        'talent__user__username',
        'talent__user__firstname',
        'talent__user__lastname',
        'content',
        'caption',
    ]
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'views_count']
    ordering = ['-created_at']
    list_per_page = 25
    actions = ['delete_selected_posts']
    
    fieldsets = (
        ('Post Information', {
            'fields': ('talent', 'content', 'caption')
        }),
        ('Media', {
            'fields': ('image', 'video'),
            'description': 'Upload image or video for the post'
        }),
        ('Statistics', {
            'fields': ('likes_count', 'views_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def post_display(self, obj):
        """Display post with media preview"""
        media_html = ""
        if obj.image:
            media_html = f'<img src="{obj.image.url}" width="40" height="40" style="border-radius: 4px; margin-right: 10px;" />'
        elif obj.video:
            media_html = f'<span style="margin-right: 10px;">🎥</span>'
        
        post_url = reverse('admin:talent_post_change', args=[obj.id])
        return format_html(
            '{}<a href="{}">Post #{}</a><br><small style="color: #666;">{}</small>',
            media_html,
            post_url,
            obj.id,
            obj.created_at.strftime("%b %d, %Y %H:%M")
        )
    post_display.short_description = "Post"
    post_display.admin_order_field = 'id'

    def talent_display(self, obj):
        """Display talent information"""
        talent_url = reverse('admin:talent_talentprofile_change', args=[obj.talent.id])
        user_url = reverse('admin:userauths_user_change', args=[obj.talent.user.id])
        return format_html(
            '<a href="{}">{}</a><br><small><a href="{}">View User</a></small>',
            talent_url,
            obj.talent.user.get_full_name(),
            user_url
        )
    talent_display.short_description = "Talent"
    talent_display.admin_order_field = 'talent__user__firstname'

    def content_preview(self, obj):
        """Show content preview"""
        if obj.content:
            preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
            return preview
        return "No content"
    content_preview.short_description = "Content Preview"

    def has_media(self, obj):
        """Show if post has media"""
        if obj.image:
            return format_html('<span style="color: green;">🖼️ Image</span>')
        elif obj.video:
            return format_html('<span style="color: blue;">🎥 Video</span>')
        return format_html('<span style="color: gray;">📝 Text only</span>')
    has_media.short_description = "Media Type"

    def likes_count(self, obj):
        """Show likes count"""
        return obj.likes.count()
    likes_count.short_description = "Likes"

    def views_count(self, obj):
        """Show views count"""
        return obj.views.count()
    views_count.short_description = "Views"

    def created_date(self, obj):
        """Display formatted creation date"""
        return obj.created_at.strftime("%b %d, %Y")
    created_date.short_description = "Created"
    created_date.admin_order_field = 'created_at'

    def delete_selected_posts(self, request, queryset):
        """Custom action to delete selected posts"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Successfully deleted {count} posts.")
    delete_selected_posts.short_description = "Delete selected posts"

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('talent__user').prefetch_related('likes', 'views')


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = [
        'like_display',
        'post_display',
        'user_display',
        'liked_date',
    ]
    list_filter = [
        'liked_at',
    ]
    search_fields = [
        'post__talent__user__username',
        'post__talent__user__firstname',
        'post__talent__user__lastname',
        'user__username',
        'user__firstname',
        'user__lastname',
    ]
    readonly_fields = ['liked_at']
    ordering = ['-liked_at']
    list_per_page = 25

    fieldsets = (
        ('Like Information', {
            'fields': ('post', 'user')
        }),
        ('Timestamp', {
            'fields': ('liked_at',),
            'classes': ('collapse',)
        }),
    )

    def like_display(self, obj):
        """Display like information"""
        like_url = reverse('admin:talent_postlike_change', args=[obj.id])
        return format_html(
            '<a href="{}">Like #{}</a><br><small style="color: #666;">{}</small>',
            like_url,
            obj.id,
            obj.liked_at.strftime("%b %d, %Y %H:%M")
        )
    like_display.short_description = "Like"
    like_display.admin_order_field = 'id'

    def post_display(self, obj):
        """Display post information"""
        post_url = reverse('admin:talent_post_change', args=[obj.post.id])
        talent_url = reverse('admin:talent_talentprofile_change', args=[obj.post.talent.id])
        return format_html(
            '<a href="{}">Post #{}</a><br><small><a href="{}">View Talent</a></small>',
            post_url,
            obj.post.id,
            talent_url
        )
    post_display.short_description = "Post"
    post_display.admin_order_field = 'post__id'

    def user_display(self, obj):
        """Display user information"""
        user_url = reverse('admin:userauths_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a><br><small style="color: #666;">@{}</small>',
            user_url,
            obj.user.get_full_name(),
            obj.user.username
        )
    user_display.short_description = "User"
    user_display.admin_order_field = 'user__firstname'

    def liked_date(self, obj):
        """Display formatted like date"""
        return obj.liked_at.strftime("%b %d, %Y")
    liked_date.short_description = "Liked"
    liked_date.admin_order_field = 'liked_at'

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('post__talent__user', 'user')


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = [
        'view_display',
        'post_display',
        'user_display',
        'viewed_date',
    ]
    list_filter = [
        'viewed_at',
    ]
    search_fields = [
        'post__talent__user__username',
        'post__talent__user__firstname',
        'post__talent__user__lastname',
        'user__username',
        'user__firstname',
        'user__lastname',
    ]
    readonly_fields = ['viewed_at']
    ordering = ['-viewed_at']
    list_per_page = 25

    fieldsets = (
        ('View Information', {
            'fields': ('post', 'user')
        }),
        ('Timestamp', {
            'fields': ('viewed_at',),
            'classes': ('collapse',)
        }),
    )

    def view_display(self, obj):
        """Display view information"""
        view_url = reverse('admin:talent_postview_change', args=[obj.id])
        return format_html(
            '<a href="{}">View #{}</a><br><small style="color: #666;">{}</small>',
            view_url,
            obj.id,
            obj.viewed_at.strftime("%b %d, %Y %H:%M")
        )
    view_display.short_description = "View"
    view_display.admin_order_field = 'id'

    def post_display(self, obj):
        """Display post information"""
        post_url = reverse('admin:talent_post_change', args=[obj.post.id])
        talent_url = reverse('admin:talent_talentprofile_change', args=[obj.post.talent.id])
        return format_html(
            '<a href="{}">Post #{}</a><br><small><a href="{}">View Talent</a></small>',
            post_url,
            obj.post.id,
            talent_url
        )
    post_display.short_description = "Post"
    post_display.admin_order_field = 'post__id'

    def user_display(self, obj):
        """Display user information"""
        user_url = reverse('admin:userauths_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a><br><small style="color: #666;">@{}</small>',
            user_url,
            obj.user.get_full_name(),
            obj.user.username
        )
    user_display.short_description = "User"
    user_display.admin_order_field = 'user__firstname'

    def viewed_date(self, obj):
        """Display formatted view date"""
        return obj.viewed_at.strftime("%b %d, %Y")
    viewed_date.short_description = "Viewed"
    viewed_date.admin_order_field = 'viewed_at'

    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('post__talent__user', 'user')
