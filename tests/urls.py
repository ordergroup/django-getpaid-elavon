from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("getpaid_elavon.urls", namespace="getpaid_elavon")),
]
