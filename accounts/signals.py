from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

MEMBER_PERMISSIONS = ["add_event", "change_event", "delete_event", "view_event"]


def member_group():
    group, created = Group.objects.get_or_create(name="Miembros")
    if created or group.permissions.count() < len(MEMBER_PERMISSIONS):
        permissions = Permission.objects.filter(
            content_type__app_label="events",
            codename__in=MEMBER_PERMISSIONS,
        )
        group.permissions.set(permissions)
    return group


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def setup_new_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        instance.groups.add(member_group())