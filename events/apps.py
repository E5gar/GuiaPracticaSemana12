from django.apps import AppConfig
from django.db.models.signals import post_migrate

DEFAULT_CATEGORIES = [
    ("Música", "violet"),
    ("Cultura y tradición", "orange"),
    ("Gastronomía", "red"),
    ("Académico", "blue"),
    ("Tecnología", "cyan"),
    ("Deporte", "green"),
    ("Aire libre", "green"),
    ("Feria y mercado", "orange"),
]


def seed_categories(sender, **kwargs):
    from .models import Category

    if Category.objects.exists():
        return
    Category.objects.bulk_create([Category(name=name, tone=tone) for name, tone in DEFAULT_CATEGORIES])


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        post_migrate.connect(seed_categories, sender=self)