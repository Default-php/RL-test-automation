from django.urls import path

from web import views


app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("results/<str:report_id>/", views.results, name="results"),
    path("reports/<str:report_id>/download/", views.download_report, name="download_report"),
]
