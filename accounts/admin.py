from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import Profile

User = get_user_model()

admin.site.unregister(User)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ("avatar_url", "district", "phone", "bio")


@admin.register(User)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "email", "district", "events_organized", "is_active", "date_joined")
    list_filter = ("is_active", "date_joined", "profile__district")
    search_fields = ("username", "first_name", "last_name", "email")
    list_select_related = ("profile",)
    fields = ("username", "first_name", "last_name", "email", "is_active", "last_login", "date_joined")
    readonly_fields = ("last_login", "date_joined")
    inlines = [ProfileInline]
    actions = ["activate_users", "deactivate_users"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(organized_total=Count("organized_events", distinct=True))

    def has_add_permission(self, request):
        return False

    @admin.display(description="Nombre completo")
    def full_name(self, obj):
        return obj.get_full_name() or "-"

    @admin.display(description="Distrito", ordering="profile__district")
    def district(self, obj):
        return getattr(getattr(obj, "profile", None), "district", "-")

    @admin.display(description="Eventos creados", ordering="organized_total")
    def events_organized(self, obj):
        return obj.organized_total

    @admin.action(description="Activar usuarios seleccionados")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} usuarios activados.")

    @admin.action(description="Desactivar usuarios seleccionados")
    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(is_superuser=True).update(is_active=False)
        self.message_user(request, f"{updated} usuarios desactivados.")