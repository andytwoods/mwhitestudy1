from django.urls import path

from . import views

app_name = "participants"

urlpatterns = [
    path("start/", views.EntryView.as_view(), name="entry"),
    path("consent/", views.ConsentView.as_view(), name="consent"),
    path("withdrawn/", views.WithdrawnView.as_view(), name="withdrawn"),
    path("error/", views.ErrorView.as_view(), name="error"),
    path("questionnaire/background/", views.BackgroundQuestionnaireView.as_view(), name="background"),
    path("questionnaire/ai-trust/", views.AITrustView.as_view(), name="ai-trust"),
    path("post-study/", views.PostStudyView.as_view(), name="post-study"),
    path("debrief/", views.DebriefView.as_view(), name="debrief"),
    path("complete/", views.CompleteView.as_view(), name="complete"),
]
