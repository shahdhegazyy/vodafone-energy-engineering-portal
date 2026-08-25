from django.urls import path
from .views import home, history

app_name = "portal"

urlpatterns = [
    path("", home, name="home"),
    path("history/", history, name="history"),
]
