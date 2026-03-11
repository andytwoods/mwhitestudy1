import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from mwhitestudy1.participants.mixins import ParticipantSessionMixin
from mwhitestudy1.trials.helpers.response_save import save_response
from mwhitestudy1.trials.helpers.trial_state import get_current_stage
from mwhitestudy1.trials.helpers.trial_state import get_current_trial
from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.models import Trial

logger = logging.getLogger(__name__)

_FEEDBACK_STAGE = "feedback"  # synthetic stage used only for routing; not stored


def _get_stage_questions(study, stage: str, condition_name: str) -> list[Question]:
    """Return active questions for a stage, filtered to those applicable to the condition."""
    qs = Question.objects.filter(study=study, stage_location=stage, is_active=True).order_by(
        "display_order"
    )
    return [q for q in qs if not q.condition_applicability or condition_name in q.condition_applicability]


def _parse_rt(request) -> int | None:
    try:
        return int(request.POST.get("stage_start_time_ms", ""))
    except (ValueError, TypeError):
        return None


def _redirect_or_htmx(request, url: str):
    """Return a full-page redirect, using HX-Redirect for HTMX requests."""
    if request.headers.get("HX-Request"):
        resp = HttpResponse()
        resp["HX-Redirect"] = url
        return resp
    return redirect(url)


class TrialView(ParticipantSessionMixin, View):
    """Single-URL HTMX-driven view for all trial stages.

    GET /study/trial/                  → resolve current trial and stage, render
    GET /study/trial/?trial_id=X&stage=feedback  → render feedback display partial
    GET /study/trial/?trial_id=X&stage=post_feedback → render post-feedback form
    POST /study/trial/                 → save responses, advance stage
    """

    def get(self, request):
        # Explicit stage navigation (e.g. from the feedback Continue button)
        explicit_stage = request.GET.get("stage")
        trial_id = request.GET.get("trial_id")

        if explicit_stage and trial_id:
            trial = get_object_or_404(Trial, pk=trial_id, participant=self.participant)
            context = self._build_context(trial, explicit_stage)
            partial = self._partial_for_stage(trial, explicit_stage)
            if request.headers.get("HX-Request"):
                return render(request, partial, context)
            return render(request, "trials/trial.html", context)

        trial = get_current_trial(self.participant)

        if trial is None:
            return _redirect_or_htmx(request, reverse("participants:post-study"))

        stage = get_current_stage(self.participant, trial)
        context = self._build_context(trial, stage)

        if request.headers.get("HX-Request"):
            return render(request, self._partial_for_stage(trial, stage), context)
        return render(request, "trials/trial.html", context)

    def post(self, request):
        trial_id = request.POST.get("trial_id")
        stage = request.POST.get("stage")
        trial = get_object_or_404(Trial, pk=trial_id, participant=self.participant)
        client_rt_ms = _parse_rt(request)

        study = self.participant.study
        questions = _get_stage_questions(study, stage, trial.condition.name)

        errors = []
        for question in questions:
            value = request.POST.get(f"q_{question.pk}", "").strip()
            if not value:
                errors.append(f"Please answer all questions before continuing.")
                break
            try:
                save_response(self.participant, trial, question, value, stage, client_rt_ms)
            except ValueError as exc:
                errors.append(str(exc))

        if errors:
            context = self._build_context(trial, stage)
            context["errors"] = errors
            return render(request, self._partial_for_stage(trial, stage), context, status=422)

        new_stage = get_current_stage(self.participant, trial)
        return self._render_next(request, trial, new_stage)

    def _render_next(self, request, current_trial: Trial, new_stage: str):
        if new_stage == Question.POST_FEEDBACK:
            # Show feedback cards before the post-feedback form
            is_feedback_condition = current_trial.condition.name != "baseline"
            if is_feedback_condition and current_trial.feedback_presented:
                context = self._build_context(current_trial, _FEEDBACK_STAGE)
                return render(request, "trials/partials/_stage_feedback.html", context)

        if new_stage == "complete":
            next_trial = get_current_trial(self.participant)

            if next_trial is None:
                return _redirect_or_htmx(request, reverse("participants:post-study"))

            # Practice → real trial transition
            if current_trial.is_practice and not next_trial.is_practice:
                return render(request, "trials/partials/_practice_complete.html", {
                    "participant": self.participant,
                })

            # Block boundary
            if (not next_trial.is_practice
                    and next_trial.block_position != current_trial.block_position):
                context = {
                    "participant": self.participant,
                    "completed_block": current_trial.block_position,
                    "total_blocks": 4,
                    "next_trial": next_trial,
                }
                return render(request, "trials/partials/_inter_block.html", context)

            return render(request, "trials/partials/_inter_trial.html", {
                "participant": self.participant,
                "trial": next_trial,
            })

        # Still within same trial (e.g. initial → post_feedback already handled above)
        context = self._build_context(current_trial, new_stage)
        return render(request, self._partial_for_stage(current_trial, new_stage), context)

    def _build_context(self, trial: Trial, stage: str) -> dict:
        study = self.participant.study
        questions = (
            _get_stage_questions(study, stage, trial.condition.name)
            if stage not in (_FEEDBACK_STAGE,)
            else []
        )
        return {
            "participant": self.participant,
            "trial": trial,
            "stage": stage,
            "questions": questions,
        }

    @staticmethod
    def _partial_for_stage(trial: Trial, stage: str) -> str:
        if stage == Question.INITIAL_JUDGEMENT:
            return "trials/partials/_stage_initial.html"
        if stage == _FEEDBACK_STAGE:
            return "trials/partials/_stage_feedback.html"
        if stage == Question.POST_FEEDBACK:
            return "trials/partials/_stage_post_feedback.html"
        return "trials/partials/_inter_trial.html"


class BlockBreakView(ParticipantSessionMixin, View):
    """Mandatory inter-block break screen."""

    def get(self, request):
        trial = get_current_trial(self.participant)
        context = {
            "participant": self.participant,
            "trial": trial,
            "completed_block": int(request.GET.get("completed_block", 0)),
            "total_blocks": 4,
        }
        if request.headers.get("HX-Request"):
            return render(request, "trials/partials/_inter_block.html", context)
        return render(request, "trials/block_break.html", context)
