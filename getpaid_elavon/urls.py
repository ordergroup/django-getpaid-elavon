from django.urls import path

from . import views

app_name = "getpaid_elavon"

urlpatterns = [
    path(
        "callback/",
        views.CallbackView.as_view(),
        name="callback",
    ),
]
