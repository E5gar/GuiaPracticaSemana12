from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("ingresar/", views.HuancaLoginView.as_view(), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
    path("registro/", views.register_view, name="register"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),
    path("perfil/<str:username>/", views.profile_view, name="profile"),
]