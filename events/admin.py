from django.contrib import admin
from django.db.models import Count

from .models import Category, Event, Reaction, Registration


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tone", "events_total")
    list_filter = ("tone",)
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total=Count("events"))

    @admin.display(description="Eventos", ordering="total")
    def events_total(self, obj):
        return obj.total


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "category", "district", "starts_at", "attendance", "price", "is_published")
    list_filter = ("is_published", "category", "district", "starts_at")
    search_fields = ("title", "venue", "organizer__username", "organizer__email")
    list_select_related = ("organizer", "category")
    date_hierarchy = "starts_at"
    readonly_fields = ("attendance", "created_at", "updated_at")
    actions = ["publish_events", "hide_events"]
    fieldsets = (
        ("Información", {"fields": ("title", "organizer", "category", "description", "cover_url")}),
        ("Lugar y fecha", {"fields": ("venue", "address", "district", "starts_at", "ends_at")}),
        ("Cupo y precio", {"fields": ("capacity", "price", "attendance", "is_published")}),
        ("Auditoría", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(attendees_total=Count("registrations", distinct=True))

    @admin.display(description="Asistencia", ordering="attendees_total")
    def attendance(self, obj):
        return f"{getattr(obj, 'attendees_total', 0)} / {obj.capacity}"

    @admin.action(description="Publicar eventos seleccionados")
    def publish_events(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} eventos publicados.")

    @admin.action(description="Ocultar eventos seleccionados")
    def hide_events(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} eventos ocultados.")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "created_at")
    list_filter = ("created_at", "event__category")
    search_fields = ("user__username", "event__title")
    list_select_related = ("user", "event")
    readonly_fields = ("created_at",)


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "kind", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("user__username", "event__title")
    list_select_related = ("user", "event")
    readonly_fields = ("created_at",)