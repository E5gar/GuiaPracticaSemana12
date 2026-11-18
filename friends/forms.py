from django import forms

from config.sanitizers import sanitize_input


class FriendSearchForm(forms.Form):
    q = forms.CharField(
        label="Buscar personas",
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "Nombre o usuario"}),
    )

    def clean_q(self):
        return sanitize_input(self.cleaned_data.get("q", ""))


class FriendActionForm(forms.Form):
    ACTIONS = [
        ("send", "Enviar solicitud"),
        ("accept", "Aceptar"),
        ("decline", "Rechazar"),
        ("cancel", "Cancelar solicitud"),
        ("remove", "Quitar amistad"),
    ]

    user_id = forms.IntegerField(min_value=1)
    action = forms.ChoiceField(choices=ACTIONS)