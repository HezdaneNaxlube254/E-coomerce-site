"""
Signals for user app.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone

from .models import User, AuditLog


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login."""
    AuditLog.objects.create(
        user=user,
        action='login',
        model_name='User',
        object_id=str(user.id),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout."""
    if user:
        AuditLog.objects.create(
            user=user,
            action='logout',
            model_name='User',
            object_id=str(user.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )


@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    """Log user creation/update."""
    action = 'create' if created else 'update'
    AuditLog.objects.create(
        user=instance,
        action=action,
        model_name='User',
        object_id=str(instance.id),
        details={
            'email': instance.email,
            'changes': getattr(instance, '_change_details', {}),
        }
    )


@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    """Track changes to user model."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            changes = {}
            for field in ['email', 'first_name', 'last_name', 'phone', 'department', 'position', 'is_active']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    changes[field] = {'old': old_value, 'new': new_value}
            instance._change_details = changes
        except User.DoesNotExist:
            instance._change_details = {}
