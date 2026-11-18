from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.home, name="home"),
    path("eventos/", views.event_list, name="list"),
    path("eventos/nuevo/", views.EventCreateView.as_view(), name="create"),
    path("eventos/<int:pk>/", views.event_detail, name="detail"),
    path("eventos/<int:pk>/editar/", views.EventUpdateView.as_view(), name="update"),
    path("eventos/<int:pk>/eliminar/", views.EventDeleteView.as_view(), name="delete"),
    path("eventos/<int:pk>/inscripcion/", views.toggle_registration, name="register"),
    path("eventos/<int:pk>/reaccion/", views.react, name="react"),
    path("mis-eventos/", views.my_events, name="mine"),
    path("mis-inscripciones/", views.my_registrations, name="registrations"),
]