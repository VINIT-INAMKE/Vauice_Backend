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
@receiver(post_save, sender='talent.TalentProfile')
def update_talent_pool_on_profile_save(sender, instance, created, **kwargs):
    """
    Automatically add/remove talent from mentor pools based on onboarding completion
    Only add talents with onboarding_done True to the pool
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    mentors = User.objects.filter(user_type='mentor')
    if hasattr(instance, 'user') and getattr(instance.user, 'onboarding_done', False):
        # Add talent to all mentor pools if not already there
        for mentor in mentors:
            TalentPool.objects.get_or_create(
                mentor=mentor,
                talent=instance.user
            )
    else:
        # Remove talent from all mentor pools if onboarding is not done
        TalentPool.objects.filter(talent=instance.user).delete()


@receiver(post_save, sender='mentor.MentorProfile')
def update_talent_pool_on_mentor_save(sender, instance, created, **kwargs):
    """
    When a new mentor is created, add all 100% complete talents to their pool
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if created:
        # Get all talents with 100% complete profiles
        talents = User.objects.filter(
            user_type='talent',
            talent_profile__is_profile_complete=True,
            talent_profile__profile_completion_percentage=100
        )
        
        # Add all complete talents to the new mentor's pool
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
