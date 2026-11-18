from django.conf import settings
from django.db import models

from .validators import validate_avatar_url, validate_phone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=280, blank=True)
    district = models.CharField(max_length=60, blank=True, default="Huancayo")
    phone = models.CharField(max_length=9, blank=True, validators=[validate_phone])
    avatar_url = models.URLField(max_length=500, blank=True, validators=[validate_avatar_url])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfiles"

    def __str__(self):
        return f"Perfil de {self.user.username}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def initial(self):
        return (self.user.first_name or self.user.username)[:1].upper()