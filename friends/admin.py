from django.contrib import admin

from .models import ACCEPTED, Friendship


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("from_user__username", "to_user__username")
    list_select_related = ("from_user", "to_user")
    readonly_fields = ("created_at",)
    actions = ["accept_selected"]

    @admin.action(description="Marcar solicitudes como aceptadas")
    def accept_selected(self, request, queryset):
        updated = queryset.update(status=ACCEPTED)
        self.message_user(request, f"{updated} solicitudes aceptadas.")