from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.urls import reverse
from django.utils import timezone

from .validators import validate_cover_url, validate_event_title

DEFAULT_COVER = "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=1200&q=80"

REACTION_META = [
    ("like", "Me gusta", "thumbs-up"),
    ("heart", "Me encanta", "heart"),
    ("sad", "Me entristece", "frown"),
    ("laugh", "Me divierte", "laugh"),
    ("angry", "Me enfurece", "angry"),
]

DISTRICTS = [
    ("Huancayo", "Huancayo"),
    ("El Tambo", "El Tambo"),
    ("Chilca", "Chilca"),
    ("Sapallanga", "Sapallanga"),
    ("Huancán", "Huancán"),
    ("Concepción", "Concepción"),
    ("Jauja", "Jauja"),
]


class Category(models.Model):
    TONES = [
        ("red", "Rojo"),
        ("blue", "Azul"),
        ("green", "Verde"),
        ("violet", "Violeta"),
        ("orange", "Naranja"),
        ("cyan", "Celeste"),
    ]

    name = models.CharField(max_length=40, unique=True)
    tone = models.CharField(max_length=10, choices=TONES, default="blue")

    class Meta:
        ordering = ["name"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.name


class EventQuerySet(models.QuerySet):
    def with_stats(self, user=None):
        reaction_counts = {
            f"{kind}_count": Count("reactions", filter=Q(reactions__kind=kind), distinct=True)
            for kind, _, _ in REACTION_META
        }
        queryset = self.select_related("organizer", "organizer__profile", "category").annotate(
            attendees_count=Count("registrations", distinct=True),
            **reaction_counts,
        )
        if user is not None and user.is_authenticated:
            queryset = queryset.annotate(
                my_reaction=Subquery(
                    Reaction.objects.filter(event=OuterRef("pk"), user=user).values("kind")[:1]
                ),
                is_registered=Exists(Registration.objects.filter(event=OuterRef("pk"), user=user)),
            )
        return queryset


class Event(models.Model):
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organized_events")
    title = models.CharField(max_length=120, validators=[validate_event_title])
    description = models.TextField(max_length=2000)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="events")
    venue = models.CharField(max_length=120)
    address = models.CharField(max_length=200, blank=True)
    district = models.CharField(max_length=60, choices=DISTRICTS, default="Huancayo")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=50, validators=[MinValueValidator(1), MaxValueValidator(5000)])
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    cover_url = models.URLField(max_length=500, blank=True, validators=[validate_cover_url])
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["starts_at"]
        verbose_name = "evento"
        verbose_name_plural = "eventos"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.pk])

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.pk and self.capacity is not None and self.capacity < self.registrations.count():
            raise ValidationError({"capacity": "El aforo no puede ser menor a la cantidad de inscritos actuales."})

    @property
    def cover(self):
        return self.cover_url or DEFAULT_COVER

    @property
    def is_free(self):
        return self.price == 0

    @property
    def is_past(self):
        return self.ends_at < timezone.now()

    @property
    def spots_left(self):
        taken = getattr(self, "attendees_count", None)
        if taken is None:
            taken = self.registrations.count()
        return self.capacity - taken

    @property
    def reactions_summary(self):
        mine = getattr(self, "my_reaction", None)
        return [
            {
                "kind": kind,
                "label": label,
                "icon": icon,
                "count": getattr(self, f"{kind}_count", 0),
                "active": mine == kind,
            }
            for kind, label, icon in REACTION_META
        ]


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_registrations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="unique_registration")]
        ordering = ["-created_at"]
        verbose_name = "inscripción"
        verbose_name_plural = "inscripciones"

    def __str__(self):
        return f"{self.user} en {self.event}"


class Reaction(models.Model):
    KINDS = [(kind, label) for kind, label, _ in REACTION_META]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_reactions")
    kind = models.CharField(max_length=10, choices=KINDS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="unique_reaction_per_user")]
        ordering = ["-created_at"]
        verbose_name = "reacción"
        verbose_name_plural = "reacciones"

    def __str__(self):
        return f"{self.user} - {self.kind} - {self.event}"