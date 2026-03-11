from django.urls import reverse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        entry_path = reverse("participants:entry")
        params = "?PROLIFIC_PID=TEST_PID&STUDY_ID=TEST_STUDY&SESSION_ID=TEST_SESSION"
        ctx["study_preview_url"] = self.request.build_absolute_uri(entry_path + params)
        ctx["study_entry_path"] = entry_path + params
        return ctx


class AboutView(TemplateView):
    template_name = "pages/about.html"
