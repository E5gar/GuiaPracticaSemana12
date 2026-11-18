from django.core.validators import RegexValidator

validate_username_format = RegexValidator(
    r"^[a-zA-Z0-9_.]{4,20}$",
    "Usa entre 4 y 20 caracteres: letras, números, punto o guion bajo.",
)

validate_person_name = RegexValidator(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]{2,60}$",
    "Solo se permiten letras y espacios, entre 2 y 60 caracteres.",
)

validate_phone = RegexValidator(
    r"^9\d{8}$",
    "Ingresa un celular peruano de 9 dígitos que empiece con 9.",
)

validate_avatar_url = RegexValidator(
    r"^https://[^\s<>]+$",
    "La imagen debe ser un enlace https válido.",
)