"""
Phase 10 — Integration test: full participant flow from entry to Prolific redirect.

Tests 47-51 from ACTIONS.md acceptance criteria.
"""
import json

import pytest
from django.core.management import call_command
from django.urls import reverse

from mwhitestudy1.images.models import Image
from mwhitestudy1.images.tests.factories import ImageFactory
from mwhitestudy1.participants.models import ConsentRecord
from mwhitestudy1.participants.models import DebriefRecord
from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.trials.helpers.trial_state import get_current_stage
from mwhitestudy1.trials.helpers.trial_state import get_current_trial
from mwhitestudy1.trials.models import FeedbackItem
from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.models import Response
from mwhitestudy1.trials.tests.factories import FeedbackItemFactory


# Small config: 2 trials per condition, wrong_rate=0 (only correct feedback needed)
_STUDY_CONFIG = {
    "study_id": "integration-study",
    "payment_gbp": 12.0,
    "practice_trial_count": 0,
    "prolific_completion_code": "TESTCODE123",
    "trials_per_condition": {"baseline": 2, "human": 2, "human_ai": 2, "ai": 2},
    "feedback_wrong_rate": 0.0,
    "feedback_consensus": "unanimous",
    "feedback_agents": {
        "human": [{"type": "human", "label": "Consultant Radiologist", "count": 1}],
        "human_ai": [
            {"type": "human", "label": "Consultant Radiologist", "count": 1},
            {"type": "ai", "label": "AI Diagnostic System", "count": 1},
        ],
        "ai": [{"type": "ai", "label": "AI Diagnostic System", "count": 1}],
    },
}


@pytest.fixture
def study_env(db, tmp_path, settings):
    """Bootstrap a complete study environment with images and feedback pool."""
    cfg_file = tmp_path / "study.json"
    cfg_file.write_text(json.dumps(_STUDY_CONFIG))
    settings.ACTIVE_STUDY_CONFIG = str(cfg_file)
    settings.BASE_DIR = ""

    import io
    call_command("bootstrap_study", stdout=io.StringIO())

    from mwhitestudy1.study.models import Study
    study = Study.objects.get(slug="integration-study")

    # 4 malignant + 4 benign = enough for 4 conditions x 1 mal + 1 ben each
    for i in range(4):
        img_mal = ImageFactory(
            external_id=f"int_mal_{i:02d}",
            ground_truth=Image.MALIGNANT,
            is_practice=False,
        )
        img_ben = ImageFactory(
            external_id=f"int_ben_{i:02d}",
            ground_truth=Image.BENIGN,
            is_practice=False,
        )
        for img, gt in [(img_mal, Image.MALIGNANT), (img_ben, Image.BENIGN)]:
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.HUMAN, diagnosis=gt)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.AI, diagnosis=gt)

    return study


def _set_session(client, participant_id):
    session = client.session
    session["participant_id"] = participant_id
    session.save()


def _trust_data():
    return {f"item_{i}": "4" for i in range(1, 13)}


def _complete_all_trials(client, participant):
    """Walk every trial, submitting the minimum valid responses for each stage."""
    study = participant.study
    q_initial = list(Question.objects.filter(
        study=study, stage_location=Question.INITIAL_JUDGEMENT, is_active=True
    ).order_by("display_order"))
    q_post = list(Question.objects.filter(
        study=study, stage_location=Question.POST_FEEDBACK, is_active=True
    ).order_by("display_order"))

    max_iterations = 200  # safety guard
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        trial = get_current_trial(participant)
        if trial is None:
            break

        stage = get_current_stage(participant, trial)

        if stage == Question.INITIAL_JUDGEMENT:
            data = {
                "trial_id": str(trial.pk),
                "stage": stage,
                "stage_start_time_ms": "1000",
            }
            for q in q_initial:
                if q.question_type in (Question.BINARY, Question.MULTIPLE_CHOICE):
                    data[f"q_{q.pk}"] = q.response_options[0]
                else:
                    data[f"q_{q.pk}"] = "50"
            client.post(reverse("trials:trial"), data)

        elif stage == Question.POST_FEEDBACK:
            applicable = [
                q for q in q_post
                if not q.condition_applicability
                or trial.condition.name in q.condition_applicability
            ]
            data = {
                "trial_id": str(trial.pk),
                "stage": stage,
                "stage_start_time_ms": "2000",
            }
            for q in applicable:
                if q.question_type in (Question.BINARY, Question.MULTIPLE_CHOICE):
                    data[f"q_{q.pk}"] = q.response_options[0]
                elif q.question_type == Question.LIKERT:
                    data[f"q_{q.pk}"] = "4"
                else:
                    data[f"q_{q.pk}"] = "50"
            client.post(reverse("trials:trial"), data)

        else:
            break  # unexpected stage


def _run_full_flow(client, prolific_pid):
    """Run the complete participant flow and return the participant."""
    entry_url = (
        reverse("participants:entry")
        + f"?PROLIFIC_PID={prolific_pid}&STUDY_ID=S1&SESSION_ID=SS1"
    )
    client.get(entry_url)
    participant = ParticipantSession.objects.get(prolific_pid=prolific_pid)
    _set_session(client, participant.pk)

    client.post(reverse("participants:consent"), {"consent_given": "true"})
    client.post(reverse("participants:background"), {"medical_training_level": "radiologist"})
    client.post(reverse("participants:ai-trust"), _trust_data())

    participant.refresh_from_db()
    _complete_all_trials(client, participant)

    client.post(
        reverse("participants:post-study"),
        {
            "noticed_feedback": "yes",
            "attention_to_feedback": "5",
            "influence_of_feedback": "4",
            "demand_awareness_response": "Testing feedback effects.",
        },
    )
    client.get(reverse("participants:debrief"))
    participant.refresh_from_db()
    return participant


@pytest.mark.django_db
def test_47_completion_status_is_complete(client, study_env):
    """Test 47: Full flow sets completion_status='complete'."""
    participant = _run_full_flow(client, "PID047")
    assert participant.completion_status == ParticipantSession.COMPLETE


@pytest.mark.django_db
def test_48_correct_response_count(client, study_env):
    """Test 48: Exactly 40 Response records created (2 initial × 8 trials + 4 post × 6 non-baseline)."""
    participant = _run_full_flow(client, "PID048")
    total = Response.objects.filter(participant=participant).count()
    # 2 initial questions × 8 trials = 16
    # 4 post-feedback questions × 6 non-baseline trials = 24
    assert total == 40, f"Expected 40 responses, got {total}"


@pytest.mark.django_db
def test_49_consent_and_debrief_records_exist(client, study_env):
    """Test 49: ConsentRecord (consent_given=True) and DebriefRecord both linked to session."""
    participant = _run_full_flow(client, "PID049")
    assert ConsentRecord.objects.filter(participant=participant, consent_given=True).exists()
    assert DebriefRecord.objects.filter(participant=participant).exists()


@pytest.mark.django_db
def test_50_median_trial_rt_positive(client, study_env):
    """Test 50: median_trial_rt is populated and > 0 after completion."""
    participant = _run_full_flow(client, "PID050")
    assert participant.median_trial_rt is not None
    assert participant.median_trial_rt > 0


@pytest.mark.django_db
def test_51_complete_url_blocked_mid_study(client, study_env):
    """Test 51: /study/complete/ before finishing redirects away; Prolific URL not served."""
    entry_url = (
        reverse("participants:entry")
        + "?PROLIFIC_PID=PID051&STUDY_ID=S1&SESSION_ID=SS5"
    )
    client.get(entry_url)
    participant = ParticipantSession.objects.get(prolific_pid="PID051")
    _set_session(client, participant.pk)
    client.post(reverse("participants:consent"), {"consent_given": "true"})

    response = client.get(reverse("participants:complete"))

    assert response.status_code == 302
    assert "app.prolific.com" not in response.get("Location", "")
    assert "TESTCODE123" not in response.content.decode()
