from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from config.sanitizers import sanitize_input

from .models import Profile
from .validators import validate_person_name, validate_username_format

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Nombres", max_length=60, validators=[validate_person_name])
    last_name = forms.CharField(label="Apellidos", max_length=60, validators=[validate_person_name])
    email = forms.EmailField(label="Correo electrónico")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["username"].help_text = "De 4 a 20 caracteres: letras, números, punto o guion bajo."
        self.fields["username"].validators.append(validate_username_format)
        self.fields["password1"].label = "Contraseña"
        self.fields["password1"].help_text = "Mínimo 8 caracteres, sin ser solo números."
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["first_name"].widget.attrs.update({"autocomplete": "given-name"})
        self.fields["last_name"].widget.attrs.update({"autocomplete": "family-name"})
        self.fields["email"].widget.attrs.update({"placeholder": "nombre@correo.com"})

    def clean_username(self):
        username = sanitize_input(self.cleaned_data.get("username", ""), lower=True)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ese nombre de usuario ya está en uso.")
        return username

    def clean_first_name(self):
        return sanitize_input(self.cleaned_data.get("first_name", "")).title()

    def clean_last_name(self):
        return sanitize_input(self.cleaned_data.get("last_name", "")).title()

    def clean_email(self):
        email = sanitize_input(self.cleaned_data.get("email", ""), lower=True)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password1")
        username = cleaned.get("username")
        if password and username and username.lower() in password.lower():
            self.add_error("password1", "La contraseña no debe contener tu nombre de usuario.")
        return cleaned


class LoginForm(AuthenticationForm):
    remember = forms.BooleanField(required=False, label="Mantener la sesión iniciada")

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos.",
        "inactive": "Esta cuenta está desactivada.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["username"].widget.attrs.update({"autofocus": True, "placeholder": "tu_usuario"})
        self.fields["password"].label = "Contraseña"

    def clean_username(self):
        return sanitize_input(self.cleaned_data.get("username", ""))


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombres", max_length=60, validators=[validate_person_name])
    last_name = forms.CharField(label="Apellidos", max_length=60, validators=[validate_person_name])

    class Meta:
        model = Profile
        fields = ["avatar_url", "district", "phone", "bio"]
        labels = {
            "avatar_url": "Foto de perfil (enlace)",
            "district": "Distrito",
            "phone": "Celular",
            "bio": "Biografía",
        }
        help_texts = {
            "avatar_url": "Pega un enlace https de una imagen. Si lo dejas vacío se mostrará tu inicial.",
            "phone": "Opcional. 9 dígitos.",
        }
        widgets = {
            "avatar_url": forms.URLInput(attrs={"placeholder": "https://"}),
            "bio": forms.Textarea(attrs={"rows": 4, "maxlength": 280}),
            "phone": forms.TextInput(attrs={"placeholder": "987654321", "inputmode": "numeric"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.order_fields(["first_name", "last_name", "avatar_url", "district", "phone", "bio"])
        if user is not None and not self.is_bound:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def clean_first_name(self):
        return sanitize_input(self.cleaned_data.get("first_name", "")).title()

    def clean_last_name(self):
        return sanitize_input(self.cleaned_data.get("last_name", "")).title()

    def clean_district(self):
        return sanitize_input(self.cleaned_data.get("district", ""))

    def clean_bio(self):
        return sanitize_input(self.cleaned_data.get("bio", ""), multiline=True)

    def clean_avatar_url(self):
        return sanitize_input(self.cleaned_data.get("avatar_url", ""))

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        if commit:
            self.user.save()
            profile.save()
        return profile