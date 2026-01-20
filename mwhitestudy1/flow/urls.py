from django.urls import path
from . import views

app_name = "flow"
urlpatterns = [
    path("<slug:study_slug>/", views.start_study, name="start"),
    path("<slug:study_slug>/screen/<str:screen_key>/", views.get_screen_fragment, name="screen"),
    path("<slug:study_slug>/answer/<str:screen_key>/", views.submit_answer, name="answer"),
]
