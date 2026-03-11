from django.urls import path

from .views import AboutView
from .views import HomeView

app_name = "pages"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
]
