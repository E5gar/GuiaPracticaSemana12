from django.urls import path

from . import views

app_name = "friends"

urlpatterns = [
    path("", views.friend_list, name="list"),
    path("buscar/", views.friend_search, name="search"),
    path("solicitudes/", views.friend_requests, name="requests"),
    path("accion/", views.friend_action, name="action"),
]