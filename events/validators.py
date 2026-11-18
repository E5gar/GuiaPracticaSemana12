from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone

validate_event_title = RegexValidator(
    r"^[\w¡!¿?.,:;()&/\-' ]{5,120}$",
    "El título tiene caracteres no permitidos o es demasiado corto.",
)

validate_cover_url = RegexValidator(
    r"^https://[^\s<>]+$",
    "La portada debe ser un enlace https válido.",
)


def validate_future_datetime(value):
    if value < timezone.now():
        raise ValidationError("La fecha de inicio debe ser futura.")