from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError

from config.sanitizers import sanitize_input

from .models import Category, Event, Reaction
from .validators import validate_future_datetime

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "category",
            "description",
            "venue",
            "address",
            "district",
            "starts_at",
            "ends_at",
            "capacity",
            "price",
            "cover_url",
        ]
        labels = {
            "title": "Título del evento",
            "category": "Categoría",
            "description": "Descripción",
            "venue": "Lugar",
            "address": "Dirección o referencia",
            "district": "Distrito",
            "starts_at": "Inicio",
            "ends_at": "Fin",
            "capacity": "Aforo máximo",
            "price": "Precio de entrada (S/)",
            "cover_url": "Portada (enlace de imagen)",
        }
        help_texts = {
            "cover_url": "Pega un enlace https de una imagen. Si lo dejas vacío usaremos una portada por defecto.",
            "price": "Usa 0 si la entrada es libre.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Festival de la Huaylarsh"}),
            "description": forms.Textarea(attrs={"rows": 6, "maxlength": 2000}),
            "venue": forms.TextInput(attrs={"placeholder": "Plaza Huamanmarca"}),
            "address": forms.TextInput(attrs={"placeholder": "Jr. Real 123, a una cuadra del parque"}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
            "capacity": forms.NumberInput(attrs={"min": 1, "max": 5000}),
            "price": forms.NumberInput(attrs={"min": 0, "step": "0.50"}),
            "cover_url": forms.URLInput(attrs={"placeholder": "https://"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].input_formats = [DATETIME_FORMAT]
        self.fields["ends_at"].input_formats = [DATETIME_FORMAT]
        self.fields["category"].empty_label = "Selecciona una categoría"

    def clean_title(self):
        title = sanitize_input(self.cleaned_data.get("title", ""))
        if len(title) < 5:
            raise ValidationError("El título debe tener al menos 5 caracteres.")
        return title

    def clean_description(self):
        description = sanitize_input(self.cleaned_data.get("description", ""), multiline=True)
        if len(description) < 20:
            raise ValidationError("Cuéntanos un poco más: mínimo 20 caracteres.")
        return description

    def clean_venue(self):
        return sanitize_input(self.cleaned_data.get("venue", ""))

    def clean_address(self):
        return sanitize_input(self.cleaned_data.get("address", ""))

    def clean_cover_url(self):
        return sanitize_input(self.cleaned_data.get("cover_url", ""))

    def clean_starts_at(self):
        starts_at = self.cleaned_data.get("starts_at")
        if starts_at and (not self.instance.pk or "starts_at" in self.changed_data):
            validate_future_datetime(starts_at)
        return starts_at

    def clean(self):
        cleaned = super().clean()
        starts_at = cleaned.get("starts_at")
        ends_at = cleaned.get("ends_at")
        if starts_at and ends_at:
            if ends_at <= starts_at:
                self.add_error("ends_at", "El fin debe ser posterior al inicio.")
            elif ends_at - starts_at > timedelta(days=3):
                raise ValidationError("Un evento no puede durar más de 3 días.")
        return cleaned


class EventFilterForm(forms.Form):
    WHEN = [("", "Cualquier fecha"), ("today", "Hoy"), ("week", "Próximos 7 días"), ("month", "Este mes")]
    PRICE = [("", "Cualquier precio"), ("free", "Gratis"), ("paid", "De pago")]

    q = forms.CharField(
        label="Buscar",
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "Concierto, feria, charla"}),
    )
    category = forms.ModelChoiceField(
        label="Categoría",
        queryset=Category.objects.all(),
        required=False,
        empty_label="Todas las categorías",
    )
    when = forms.ChoiceField(label="Fecha", choices=WHEN, required=False)
    price = forms.ChoiceField(label="Precio", choices=PRICE, required=False)

    def clean_q(self):
        return sanitize_input(self.cleaned_data.get("q", ""))


class ReactionForm(forms.Form):
    kind = forms.ChoiceField(choices=Reaction.KINDS)


class ActionForm(forms.Form):
    pass