from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver


class TalentPool(models.Model):
    """Pool of available talents for each mentor"""
    
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='talent_pool',
        limit_choices_to={'user_type': 'mentor'}
    )
    talent = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mentor_pools',
        limit_choices_to={'user_type': 'talent'}
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Talent Pool')
        verbose_name_plural = _('Talent Pools')
        db_table = 'talent_pools'
        unique_together = ['mentor', 'talent']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.mentor.get_full_name()} - {self.talent.get_full_name()}"


class MentorTalentSelection(models.Model):
    """Mentor's selection (acceptance) of a talent"""
    
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='talent_selections',
        limit_choices_to={'user_type': 'mentor'}
    )
    
    talent = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mentor_selections',
        limit_choices_to={'user_type': 'talent'}
    )
    selected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Mentor Talent Selection')
        verbose_name_plural = _('Mentor Talent Selections')
        db_table = 'mentor_talent_selections'
        unique_together = ['mentor', 'talent']
        ordering = ['-selected_at']
    
    def __str__(self):
        return f"{self.mentor.get_full_name()} selected {self.talent.get_full_name()}"


class MentorTalentRejection(models.Model):
    """Mentor's rejection of a talent"""
    
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='talent_rejections',
        limit_choices_to={'user_type': 'mentor'}
    )
    talent = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mentor_rejections',
        limit_choices_to={'user_type': 'talent'}
    )
    rejected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Mentor Talent Rejection')
        verbose_name_plural = _('Mentor Talent Rejections')
        db_table = 'mentor_talent_rejections'
        unique_together = ['mentor', 'talent']
        ordering = ['-rejected_at']
    
    def __str__(self):
        return f"{self.mentor.get_full_name()} rejected {self.talent.get_full_name()}"


# Signal handlers to manage talent pool automatically
@receiver(post_save, sender='userauths.User')
def update_talent_pool_on_user_onboarding_change(sender, instance, created, update_fields, **kwargs):
    """
    Automatically add/remove talent from mentor pools when onboarding_done status changes
    This ensures talent pool is managed based on actual onboarding completion
    """
    # Only handle talent users
    if instance.user_type != 'talent':
        return
    
    # Only proceed if onboarding_done field was updated
    if update_fields and 'onboarding_done' not in update_fields:
        return
        
    # Only proceed if user has a talent profile
    if not hasattr(instance, 'talent_profile'):
        return
        
    from django.contrib.auth import get_user_model
    User = get_user_model()
    mentors = User.objects.filter(user_type='mentor')
    
    if instance.onboarding_done:
        # Add talent to all mentor pools if not already there
        for mentor in mentors:
            TalentPool.objects.get_or_create(
                mentor=mentor,
                talent=instance
            )
    else:
        # Remove talent from all mentor pools if onboarding is not done
        TalentPool.objects.filter(talent=instance).delete()


@receiver(post_save, sender='mentor.MentorProfile')
def update_talent_pool_on_mentor_save(sender, instance, created, **kwargs):
    """
    When a new mentor is created, add all talents to their pool (profile completion logic removed)
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if created:
        # Get all talents
        talents = User.objects.filter(user_type='talent')
        
        # Add all talents to the new mentor's pool
        for talent in talents:
            TalentPool.objects.get_or_create(
                mentor=instance.user,
                talent=talent
            )


# Signal handlers to manage talent pool when mentors make decisions
@receiver(post_save, sender='core.MentorTalentSelection')
def remove_talent_from_pool_on_selection(sender, instance, created, **kwargs):
    """
    When a mentor selects a talent, remove that talent from that mentor's pool
    (But keep them in other mentors' pools)
    """
    if created:
        # Remove talent from this specific mentor's pool only
        TalentPool.objects.filter(
            mentor=instance.mentor,
            talent=instance.talent
        ).delete()


@receiver(post_save, sender='core.MentorTalentRejection')
def remove_talent_from_pool_on_rejection(sender, instance, created, **kwargs):
    """
    When a mentor rejects a talent, remove that talent from that mentor's pool
    (But keep them in other mentors' pools)
    """
    if created:
        # Remove talent from this specific mentor's pool only
        TalentPool.objects.filter(
            mentor=instance.mentor,
            talent=instance.talent
        ).delete()
