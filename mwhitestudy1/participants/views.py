import statistics
import logging

from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from mwhitestudy1.participants.forms import AITrustForm
from mwhitestudy1.participants.forms_post_study import DemandAwarenessForm
from mwhitestudy1.participants.forms_post_study import ManipulationCheckForm
from mwhitestudy1.participants.forms import MedicalBackgroundForm
from mwhitestudy1.participants.mixins import ParticipantSessionMixin
from mwhitestudy1.participants.models import ConsentRecord
from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.participants.models import DebriefRecord
from mwhitestudy1.participants.models import PostStudyMeasure
from mwhitestudy1.participants.models import PreStudyMeasure
from mwhitestudy1.study.helpers.config_loader import get_or_create_active_study
from mwhitestudy1.trials.helpers.session_init import initialise_participant_session

logger = logging.getLogger(__name__)


class EntryView(View):
    """Capture Prolific URL parameters, create a ParticipantSession, redirect to consent."""

    def get(self, request):
        prolific_pid = request.GET.get("PROLIFIC_PID", "").strip()
        prolific_study_id = request.GET.get("STUDY_ID", "").strip()
        prolific_session_id = request.GET.get("SESSION_ID", "").strip()

        if not all([prolific_pid, prolific_study_id, prolific_session_id]):
            return render(
                request,
                "participants/entry_error.html",
                {"message": "Required study parameters are missing. Please return to Prolific and try again."},
                status=200,
            )

        study = get_or_create_active_study()

        if ParticipantSession.objects.filter(
            prolific_pid=prolific_pid,
            study=study,
            completion_status=ParticipantSession.COMPLETE,
        ).exists():
            return render(
                request,
                "participants/entry_error.html",
                {"message": "It looks like you have already completed this study. Thank you for your participation."},
                status=200,
            )

        if not request.session.session_key:
            request.session.create()

        participant = ParticipantSession.objects.create(
            study=study,
            prolific_pid=prolific_pid,
            prolific_study_id=prolific_study_id,
            prolific_session_id=prolific_session_id,
            ip_address=request.META.get("REMOTE_ADDR"),
            django_session_key=request.session.session_key,
            completion_status=ParticipantSession.IN_PROGRESS,
            study_version=study.config_json,
        )

        request.session["participant_id"] = participant.pk
        logger.info("Created ParticipantSession pk=%d for PID=%s", participant.pk, prolific_pid)

        return redirect(reverse("participants:consent"))


class ConsentView(ParticipantSessionMixin, View):
    """Display consent form and record the participant's decision."""

    def get(self, request):
        return render(request, "participants/consent.html", {"participant": self.participant})

    def post(self, request):
        consent_given = request.POST.get("consent_given") == "true"
        study = self.participant.study

        ConsentRecord.objects.create(
            participant=self.participant,
            consent_html=study.consent_html,
            consent_version=study.consent_version,
            consent_given=consent_given,
        )

        if not consent_given:
            self.participant.completion_status = ParticipantSession.PARTIAL
            self.participant.save(update_fields=["completion_status"])
            del request.session["participant_id"]
            if request.headers.get("HX-Request"):
                return render(request, "participants/partials/_withdrawn.html")
            return redirect(reverse("participants:withdrawn"))

        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = reverse("participants:background")
            return response
        return redirect(reverse("participants:background"))


class WithdrawnView(TemplateView):
    template_name = "participants/withdrawn.html"


class ErrorView(TemplateView):
    template_name = "participants/entry_error.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("message", "An error occurred.")
        return ctx


class BackgroundQuestionnaireView(ParticipantSessionMixin, View):
    """Collect medical training level."""

    def get(self, request):
        form = MedicalBackgroundForm()
        return render(request, "participants/background.html", {"form": form})

    def post(self, request):
        form = MedicalBackgroundForm(request.POST)
        if not form.is_valid():
            if request.headers.get("HX-Request"):
                return render(request, "participants/partials/_background_form.html", {"form": form})
            return render(request, "participants/background.html", {"form": form})

        PreStudyMeasure.objects.update_or_create(
            participant=self.participant,
            defaults={"medical_training_level": form.cleaned_data["medical_training_level"]},
        )

        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = reverse("participants:ai-trust")
            return response
        return redirect(reverse("participants:ai-trust"))


class AITrustView(ParticipantSessionMixin, View):
    """Collect Jian et al. AI trust scale (12 items, 1–7 Likert)."""

    def get(self, request):
        form = AITrustForm()
        return render(request, "participants/ai_trust.html", {"form": form})

    def post(self, request):
        form = AITrustForm(request.POST)
        if not form.is_valid():
            if request.headers.get("HX-Request"):
                return render(request, "participants/partials/_ai_trust_form.html", {"form": form})
            return render(request, "participants/ai_trust.html", {"form": form})

        PreStudyMeasure.objects.update_or_create(
            participant=self.participant,
            defaults={
                "ai_trust_pre_score": form.compute_score(),
                "ai_trust_items": form.get_item_responses(),
            },
        )

        initialise_participant_session(self.participant)

        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = reverse("trials:trial")
            return response
        return redirect(reverse("trials:trial"))


class PostStudyView(ParticipantSessionMixin, View):
    """Collect post-study measures in two steps."""

    def get(self, request):
        manipulation_form = ManipulationCheckForm()
        demand_form = DemandAwarenessForm()
        return render(request, "participants/post_study.html", {
            "manipulation_form": manipulation_form,
            "demand_form": demand_form,
        })

    def post(self, request):
        manipulation_form = ManipulationCheckForm(request.POST)
        demand_form = DemandAwarenessForm(request.POST)

        if not manipulation_form.is_valid() or not demand_form.is_valid():
            return render(request, "participants/post_study.html", {
                "manipulation_form": manipulation_form,
                "demand_form": demand_form,
            })

        md = manipulation_form.cleaned_data
        dd = demand_form.cleaned_data
        PostStudyMeasure.objects.update_or_create(
            participant=self.participant,
            defaults={
                "noticed_feedback": md["noticed_feedback"],
                "attention_to_feedback": md["attention_to_feedback"],
                "influence_of_feedback": md["influence_of_feedback"],
                "demand_awareness_response": dd["demand_awareness_response"],
            },
        )
        return redirect(reverse("participants:debrief"))


class DebriefView(ParticipantSessionMixin, View):
    """Display debrief, mark session complete, store median RT."""

    def get(self, request):
        study = self.participant.study
        DebriefRecord.objects.get_or_create(
            participant=self.participant,
            defaults={
                "debrief_html": study.debrief_html,
                "debrief_version": study.debrief_version,
            },
        )
        # Compute median RT
        from mwhitestudy1.trials.models import Response as TrialResponse
        rt_values = list(
            TrialResponse.objects.filter(
                participant=self.participant,
                client_rt_ms__isnull=False,
            ).values_list("client_rt_ms", flat=True)
        )
        median_rt = statistics.median(rt_values) if rt_values else None

        from django.utils import timezone
        self.participant.completion_status = ParticipantSession.COMPLETE
        self.participant.completion_timestamp = timezone.now()
        self.participant.median_trial_rt = median_rt
        self.participant.save(update_fields=["completion_status", "completion_timestamp", "median_trial_rt"])

        return render(request, "participants/debrief.html", {
            "participant": self.participant,
            "study": study,
        })


class CompleteView(View):
    """Redirect to Prolific completion URL. Only reachable if study is complete."""

    def get(self, request):
        participant_id = request.session.get("participant_id")
        if not participant_id:
            return redirect(reverse("participants:entry"))
        try:
            participant = ParticipantSession.objects.get(pk=participant_id)
        except ParticipantSession.DoesNotExist:
            return redirect(reverse("participants:entry"))
        if participant.completion_status != ParticipantSession.COMPLETE:
            return redirect(reverse("participants:debrief"))
        code = participant.study.config_json.get("prolific_completion_code", "")
        return redirect(f"https://app.prolific.com/submissions/complete?cc={code}")
