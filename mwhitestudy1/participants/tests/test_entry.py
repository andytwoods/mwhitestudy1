import pytest
from django.urls import reverse

from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.study.tests.factories import StudyFactory


def _entry_url(pid="PID001", study_id="STUDY001", session_id="SESSION001"):
    base = reverse("participants:entry")
    return f"{base}?PROLIFIC_PID={pid}&STUDY_ID={study_id}&SESSION_ID={session_id}"


@pytest.fixture
def active_study(db, tmp_path, settings):
    import json
    config = {
        "study_id": "test-study",
        "trials_per_condition": {"baseline": 4},
        "feedback_wrong_rate": 0.25,
        "feedback_consensus": "unanimous",
        "feedback_agents": {},
        "practice_trial_count": 0,
        "prolific_completion_code": "CODE",
        "payment_gbp": 12.0,
    }
    cfg_file = tmp_path / "s.json"
    cfg_file.write_text(json.dumps(config))
    settings.ACTIVE_STUDY_CONFIG = str(cfg_file)
    settings.BASE_DIR = ""
    return StudyFactory(slug="test-study", config_json=config)


@pytest.mark.django_db
def test_entry_valid_params_creates_session(client, active_study):
    """Valid Prolific params create a ParticipantSession and redirect to consent."""
    response = client.get(_entry_url())

    assert response.status_code == 302
    assert response["Location"] == reverse("participants:consent")
    assert ParticipantSession.objects.count() == 1
    assert client.session.get("participant_id") == ParticipantSession.objects.first().pk


@pytest.mark.django_db
def test_entry_missing_param_returns_error_page(client, active_study):
    """Missing PROLIFIC_PID renders error page with 200, no session created."""
    url = reverse("participants:entry") + "?STUDY_ID=S&SESSION_ID=X"
    response = client.get(url)

    assert response.status_code == 200
    assert ParticipantSession.objects.count() == 0


@pytest.mark.django_db
def test_entry_duplicate_complete_pid_rejected(client, active_study):
    """PID with existing complete session gets error page, no new session created."""
    ParticipantSession.objects.create(
        study=active_study,
        prolific_pid="PID001",
        prolific_study_id="STUDY001",
        prolific_session_id="SESSION001",
        django_session_key="somekey",
        completion_status=ParticipantSession.COMPLETE,
    )

    response = client.get(_entry_url("PID001"))

    assert response.status_code == 200
    assert ParticipantSession.objects.count() == 1  # no new one created


@pytest.mark.django_db
def test_entry_partial_pid_creates_new_session(client, active_study):
    """PID with existing partial session is allowed to re-enter; new session created."""
    ParticipantSession.objects.create(
        study=active_study,
        prolific_pid="PID002",
        prolific_study_id="STUDY001",
        prolific_session_id="SESSION001",
        django_session_key="somekey",
        completion_status=ParticipantSession.PARTIAL,
    )

    response = client.get(_entry_url("PID002"))

    assert response.status_code == 302
    assert ParticipantSession.objects.filter(prolific_pid="PID002").count() == 2
