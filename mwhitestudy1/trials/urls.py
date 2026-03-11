from django.urls import path

from . import views

app_name = "trials"

urlpatterns = [
    path("trial/", views.TrialView.as_view(), name="trial"),
    path("break/", views.BlockBreakView.as_view(), name="block-break"),
]
