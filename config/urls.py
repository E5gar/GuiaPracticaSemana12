from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "HuancaEvent"
admin.site.site_title = "HuancaEvent"
admin.site.index_title = "Administración de la plataforma"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("accounts.urls")),
    path("amigos/", include("friends.urls")),
    path("", include("events.urls")),
]