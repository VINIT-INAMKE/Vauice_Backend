from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import TalentPool, MentorTalentSelection, MentorTalentRejection


@admin.register(TalentPool)
class TalentPoolAdmin(admin.ModelAdmin):
    list_display = [
        'mentor_display', 
        'talent_display', 
        'talent_sports', 
        'talent_location',
        'talent_completion_status',
        'added_at_formatted'
    ]
    list_filter = [
        'added_at',
        ('mentor__mentor_profile__primary_sport', admin.EmptyFieldListFilter),
        ('talent__talent_profile__primary_sport', admin.EmptyFieldListFilter),
        ('talent__talent_profile__location', admin.EmptyFieldListFilter),
        'mentor__mentor_profile__is_verified',
        'talent__talent_profile__is_verified',
    ]
    search_fields = [
        'mentor__email', 'mentor__first_name', 'mentor__last_name', 
        'talent__email', 'talent__first_name', 'talent__last_name',
        'mentor__mentor_profile__primary_sport',
        'talent__talent_profile__primary_sport',
        'talent__talent_profile__location'
    ]
    readonly_fields = ['added_at']
    ordering = ['-added_at']
    list_per_page = 25
    
    # Custom actions
    actions = ['remove_from_pool', 'export_pool_data']
    
    def mentor_display(self, obj):
        """Display mentor with verification status and link"""
        mentor = obj.mentor
        verified_icon = "✅" if mentor.mentor_profile.is_verified else "❌"
        mentor_url = reverse('admin:userauths_user_change', args=[mentor.id])
        return format_html(
            '<a href="{}">{} {} {}</a>',
            mentor_url,
            verified_icon,
            mentor.get_full_name(),
            f"({mentor.email})"
        )
    mentor_display.short_description = "Mentor"
    mentor_display.admin_order_field = 'mentor__first_name'
    
    def talent_display(self, obj):
        """Display talent with verification status and link"""
        talent = obj.talent
        verified_icon = "✅" if talent.talent_profile.is_verified else "❌"
        talent_url = reverse('admin:userauths_user_change', args=[talent.id])
        return format_html(
            '<a href="{}">{} {} {}</a>',
            talent_url,
            verified_icon,
            talent.get_full_name(),
            f"({talent.email})"
        )
    talent_display.short_description = "Talent"
    talent_display.admin_order_field = 'talent__first_name'
    
    def talent_sports(self, obj):
        """Display talent's sports"""
        sports = obj.talent.talent_profile.selected_sports
        if sports:
            return ", ".join(sports[:3]) + ("..." if len(sports) > 3 else "")
        return "No sports selected"
    talent_sports.short_description = "Talent Sports"
    
    def talent_location(self, obj):
        """Display talent's location"""
        location = obj.talent.talent_profile.location
        return location if location else "Location not set"
    talent_location.short_description = "Location"
    
    def talent_completion_status(self, obj):
        """Display talent's profile completion with color coding"""
        completion = obj.talent.talent_profile.profile_completion_percentage
        if completion == 100:
            color = "green"
            icon = "✅"
        elif completion >= 80:
            color = "orange"
            icon = "⚠️"
        else:
            color = "red"
            icon = "❌"
        
        return format_html(
            '<span style="color: {};">{} {}%</span>',
            color, icon, completion
        )
    talent_completion_status.short_description = "Profile Completion"
    talent_completion_status.admin_order_field = 'talent__talent_profile__profile_completion_percentage'
    
    def added_at_formatted(self, obj):
        """Display formatted date"""
        return obj.added_at.strftime("%b %d, %Y %H:%M")
    added_at_formatted.short_description = "Added Date"
    added_at_formatted.admin_order_field = 'added_at'
    
    def remove_from_pool(self, request, queryset):
        """Custom action to remove talents from pool"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Successfully removed {count} talents from pools.")
    remove_from_pool.short_description = "Remove selected talents from pools"
    
    def export_pool_data(self, request, queryset):
        """Custom action to export pool data"""
        # This would typically generate a CSV or Excel file
        self.message_user(request, f"Export functionality for {queryset.count()} records would be implemented here.")
    export_pool_data.short_description = "Export pool data"
    
    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related(
            'mentor__mentor_profile',
            'talent__talent_profile'
        )


@admin.register(MentorTalentSelection)
class MentorTalentSelectionAdmin(admin.ModelAdmin):
    list_display = [
        'mentor_display', 
        'talent_display', 
        'sports_match_status',
        'selection_date_formatted',
        'days_since_selection'
    ]
    list_filter = [
        'selected_at',
        ('mentor__mentor_profile__primary_sport', admin.EmptyFieldListFilter),
        ('talent__talent_profile__primary_sport', admin.EmptyFieldListFilter),
        'mentor__mentor_profile__is_verified',
        'talent__talent_profile__is_verified',
    ]
    search_fields = [
        'mentor__email', 'mentor__first_name', 'mentor__last_name', 
        'talent__email', 'talent__first_name', 'talent__last_name',
        'mentor__mentor_profile__primary_sport',
        'talent__talent_profile__primary_sport'
    ]
    readonly_fields = ['selected_at']
    ordering = ['-selected_at']
    list_per_page = 25
    
    # Custom actions
    actions = ['export_selections_data']
    
    def mentor_display(self, obj):
        """Display mentor with verification status and link"""
        mentor = obj.mentor
        verified_icon = "✅" if mentor.mentor_profile.is_verified else "❌"
        mentor_url = reverse('admin:userauths_user_change', args=[mentor.id])
        return format_html(
            '<a href="{}">{} {} {}</a>',
            mentor_url,
            verified_icon,
            mentor.get_full_name(),
            f"({mentor.email})"
        )
    mentor_display.short_description = "Mentor"
    mentor_display.admin_order_field = 'mentor__first_name'
    
    def talent_display(self, obj):
        """Display talent with verification status and link"""
        talent = obj.talent
        verified_icon = "✅" if talent.talent_profile.is_verified else "❌"
        talent_url = reverse('admin:userauths_user_change', args=[talent.id])
        return format_html(
            '<a href="{}">{} {} {}</a>',
            talent_url,
            verified_icon,
            talent.get_full_name(),
            f"({talent.email})"
        )
    talent_display.short_description = "Talent"
    talent_display.admin_order_field = 'talent__first_name'
    
    def sports_match_status(self, obj):
        """Display if mentor and talent sports match"""
        mentor_sports = set(obj.mentor.mentor_profile.selected_sports)
        talent_sports = set(obj.talent.talent_profile.selected_sports)
        common_sports = mentor_sports.intersection(talent_sports)
        
        if common_sports:
            return format_html(
                '<span style="color: green;">✅ Match: {}</span>',
                ", ".join(list(common_sports)[:2])
            )
        else:
            return format_html('<span style="color: red;">❌ No Match</span>')
    sports_match_status.short_description = "Sports Match"
    
    def selection_date_formatted(self, obj):
        """Display formatted selection date"""
        return obj.selected_at.strftime("%b %d, %Y %H:%M")
    selection_date_formatted.short_description = "Selection Date"
    selection_date_formatted.admin_order_field = 'selected_at'
    
    def days_since_selection(self, obj):
        """Display days since selection"""
        days = (timezone.now() - obj.selected_at).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        else:
            return f"{days} days ago"
    days_since_selection.short_description = "Days Since Selection"
    
    def export_selections_data(self, request, queryset):
        """Custom action to export selections data"""
        self.message_user(request, f"Export functionality for {queryset.count()} selections would be implemented here.")
    export_selections_data.short_description = "Export selections data"
    
    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related(
            'mentor__mentor_profile',
            'talent__talent_profile'
        )


@admin.register(MentorTalentRejection)
class MentorTalentRejectionAdmin(admin.ModelAdmin):
    list_display = [
        'mentor_display', 
        'talent_display', 
        'sports_match_status',
        'rejection_date_formatted',
        'days_since_rejection'
    ]
    list_filter = [
        'rejected_at',
        ('mentor__mentor_profile__primary_sport', admin.EmptyFieldListFilter),
        ('talent__talent_profile__primary_sport', admin.EmptyFieldListFilter),
        'mentor__mentor_profile__is_verified',
        'talent__talent_profile__is_verified',
    ]
    search_fields = [
        'mentor__email', 'mentor__first_name', 'mentor__last_name', 
        'talent__email', 'talent__first_name', 'talent__last_name',
        'mentor__mentor_profile__primary_sport',
        'talent__talent_profile__primary_sport'
    ]
    readonly_fields = ['rejected_at']
    ordering = ['-rejected_at']
    list_per_page = 25
    
    # Custom actions
    actions = ['export_rejections_data']
    
    def mentor_display(self, obj):
        """Display mentor with verification status and link"""
        mentor = obj.mentor
        verified_icon = "✅" if mentor.mentor_profile.is_verified else "❌"
        mentor_url = reverse('admin:userauths_user_change', args=[mentor.id])
        return format_html(
            '<a href="{}">{} {} {}</a>',
            mentor_url,
            verified_icon,
            mentor.get_full_name(),
            f"({mentor.email})"
        )
    mentor_display.short_description = "Mentor"
    mentor_display.admin_order_field = 'mentor__first_name'
    
    def talent_display(self, obj):
        """Display talent with verification status and link"""
        talent = obj.talent
        verified_icon = "✅" if talent.talent_profile.is_verified else "❌"
        talent_url = reverse('admin:userauths_user_change', args=[talent.id])
        return format_html(
            '<a href="{}">{} {} {}</a>',
            talent_url,
            verified_icon,
            talent.get_full_name(),
            f"({talent.email})"
        )
    talent_display.short_description = "Talent"
    talent_display.admin_order_field = 'talent__first_name'
    
    def sports_match_status(self, obj):
        """Display if mentor and talent sports match"""
        mentor_sports = set(obj.mentor.mentor_profile.selected_sports)
        talent_sports = set(obj.talent.talent_profile.selected_sports)
        common_sports = mentor_sports.intersection(talent_sports)
        
        if common_sports:
            return format_html(
                '<span style="color: orange;">⚠️ Match: {}</span>',
                ", ".join(list(common_sports)[:2])
            )
        else:
            return format_html('<span style="color: red;">❌ No Match</span>')
    sports_match_status.short_description = "Sports Match"
    
    def rejection_date_formatted(self, obj):
        """Display formatted rejection date"""
        return obj.rejected_at.strftime("%b %d, %Y %H:%M")
    rejection_date_formatted.short_description = "Rejection Date"
    rejection_date_formatted.admin_order_field = 'rejected_at'
    
    def days_since_rejection(self, obj):
        """Display days since rejection"""
        days = (timezone.now() - obj.rejected_at).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        else:
            return f"{days} days ago"
    days_since_rejection.short_description = "Days Since Rejection"
    
    def export_rejections_data(self, request, queryset):
        """Custom action to export rejections data"""
        self.message_user(request, f"Export functionality for {queryset.count()} rejections would be implemented here.")
    export_rejections_data.short_description = "Export rejections data"
    
    # Custom admin methods
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related(
            'mentor__mentor_profile',
            'talent__talent_profile'
        )


# Custom admin site configuration
admin.site.site_header = "Vauice Sports App Administration"
admin.site.site_title = "Vauice Admin"
admin.site.index_title = "Welcome to Vauice Sports App Administration"

# Add custom admin actions for analytics
class MatchingAnalyticsAdmin(admin.ModelAdmin):
    """Custom admin for matching analytics"""
    
    def changelist_view(self, request, extra_context=None):
        """Add analytics to the changelist view"""
        extra_context = extra_context or {}
        
        # Get analytics data
        total_pool_entries = TalentPool.objects.count()
        total_selections = MentorTalentSelection.objects.count()
        total_rejections = MentorTalentRejection.objects.count()
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_selections = MentorTalentSelection.objects.filter(selected_at__gte=week_ago).count()
        recent_rejections = MentorTalentRejection.objects.filter(rejected_at__gte=week_ago).count()
        
        # Top mentors by selections
        top_mentors = MentorTalentSelection.objects.values('mentor__first_name', 'mentor__last_name')\
            .annotate(selection_count=Count('id'))\
            .order_by('-selection_count')[:5]
        
        extra_context.update({
            'total_pool_entries': total_pool_entries,
            'total_selections': total_selections,
            'total_rejections': total_rejections,
            'recent_selections': recent_selections,
            'recent_rejections': recent_rejections,
            'top_mentors': top_mentors,
        })
        
        return super().changelist_view(request, extra_context)
