from django.urls import path
from .views import dashboard, save_design

app_name = "rack_design"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("save/", save_design, name="save_design"),
]
