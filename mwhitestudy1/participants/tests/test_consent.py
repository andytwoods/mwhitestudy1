import pytest
from django.urls import reverse

from mwhitestudy1.participants.models import ConsentRecord
from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.participants.models import PreStudyMeasure
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory


def _set_session(client, participant):
    session = client.session
    session["participant_id"] = participant.pk
    session.save()


@pytest.mark.django_db
def test_consent_given_creates_record_and_redirects(client):
    """consent_given=true creates ConsentRecord and redirects to background."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)

    response = client.post(reverse("participants:consent"), {"consent_given": "true"})

    assert response.status_code == 302
    assert response["Location"] == reverse("participants:background")
    record = ConsentRecord.objects.get(participant=participant)
    assert record.consent_given is True


@pytest.mark.django_db
def test_consent_refused_creates_record_and_withdraws(client):
    """consent_given=false creates ConsentRecord with False, redirects to withdrawn."""
    participant = ParticipantSessionFactory()
    _set_session(client, participant)

    response = client.post(reverse("participants:consent"), {"consent_given": "false"})

    assert response.status_code == 302
    assert response["Location"] == reverse("participants:withdrawn")
    record = ConsentRecord.objects.get(participant=participant)
    assert record.consent_given is False
    participant.refresh_from_db()
    assert participant.completion_status == ParticipantSession.PARTIAL
    assert PreStudyMeasure.objects.filter(participant=participant).count() == 0


@pytest.mark.django_db
def test_consent_no_session_redirects_to_entry(client):
    """GET consent with no participant_id in session redirects to entry."""
    response = client.get(reverse("participants:consent"))

    assert response.status_code == 302
    assert response["Location"] == reverse("participants:entry")
