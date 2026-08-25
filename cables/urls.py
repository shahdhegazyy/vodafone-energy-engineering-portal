from django.urls import path
from .views import dashboard, download_batch_results, download_batch_template, on_site_recommendation

app_name = "cables"
urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("batch/template/", download_batch_template, name="batch_template"),
    path("batch/results/", download_batch_results, name="batch_results"),
    path("on-site-recommendation/", on_site_recommendation, name="on_site_recommendation"),
]
