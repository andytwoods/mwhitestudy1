from unittest.mock import patch

import pytest
from django.urls import reverse

from mwhitestudy1.participants.models import PreStudyMeasure
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory


def _set_session(client, participant):
    session = client.session
    session["participant_id"] = participant.pk
    session.save()


def _valid_trust_data():
    return {f"item_{i}": "4" for i in range(1, 13)}


@pytest.mark.django_db
def test_ai_trust_valid_submission_saves_score(client):
    """All 12 items in range 1-7 saves PreStudyMeasure with correct mean score."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)
    data = {f"item_{i}": str(i % 7 + 1) for i in range(1, 13)}
    expected_mean = round(sum(int(v) for v in data.values()) / 12, 4)

    with patch("mwhitestudy1.participants.views.initialise_participant_session"):
        client.post(reverse("participants:ai-trust"), data)

    measure = PreStudyMeasure.objects.get(participant=participant)
    assert abs(measure.ai_trust_pre_score - expected_mean) < 0.0001


@pytest.mark.django_db
def test_ai_trust_item_value_zero_rejected(client):
    """Item value of 0 (below range) is invalid; no PreStudyMeasure created."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)
    data = _valid_trust_data()
    data["item_1"] = "0"

    response = client.post(reverse("participants:ai-trust"), data)

    assert response.status_code == 200
    assert PreStudyMeasure.objects.filter(participant=participant).count() == 0


@pytest.mark.django_db
def test_ai_trust_item_value_eight_rejected(client):
    """Item value of 8 (above range) is invalid; no PreStudyMeasure created."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)
    data = _valid_trust_data()
    data["item_6"] = "8"

    response = client.post(reverse("participants:ai-trust"), data)

    assert response.status_code == 200
    assert PreStudyMeasure.objects.filter(participant=participant).count() == 0


@pytest.mark.django_db
def test_background_valid_submission_saves_level(client):
    """Valid medical_training_level is saved to PreStudyMeasure."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)

    client.post(reverse("participants:background"), {"medical_training_level": "radiologist"})

    measure = PreStudyMeasure.objects.get(participant=participant)
    assert measure.medical_training_level == "radiologist"


@pytest.mark.django_db
def test_background_invalid_choice_rejected(client):
    """Invalid choice for medical_training_level re-renders the form."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)

    response = client.post(reverse("participants:background"), {"medical_training_level": "wizard"})

    assert response.status_code == 200
    assert PreStudyMeasure.objects.filter(participant=participant).count() == 0
