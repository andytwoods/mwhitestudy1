import pytest

from mwhitestudy1.participants.helpers.attention import evaluate_attention_check
from mwhitestudy1.participants.models import AttentionCheckResponse
from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory


@pytest.mark.django_db
def test_correct_response_passes_and_does_not_increment():
    """Correct response returns True and leaves attention_checks_failed unchanged."""
    participant = ParticipantSessionFactory()

    result = evaluate_attention_check(
        participant, 1, AttentionCheckResponse.IMC, "strongly_disagree", "strongly_disagree"
    )

    assert result is True
    participant.refresh_from_db()
    assert participant.attention_checks_failed == 0
    assert AttentionCheckResponse.objects.get(participant=participant, check_number=1).passed is True


@pytest.mark.django_db
def test_wrong_response_fails_and_increments():
    """Wrong response returns False and increments attention_checks_failed to 1."""
    participant = ParticipantSessionFactory()

    result = evaluate_attention_check(
        participant, 1, AttentionCheckResponse.IMC, "strongly_agree", "strongly_disagree"
    )

    assert result is False
    participant.refresh_from_db()
    assert participant.attention_checks_failed == 1
    assert AttentionCheckResponse.objects.get(participant=participant, check_number=1).passed is False


@pytest.mark.django_db
def test_two_failures_sets_excluded_inattentive():
    """Failing two checks sets excluded_inattentive=True."""
    participant = ParticipantSessionFactory()

    evaluate_attention_check(participant, 1, AttentionCheckResponse.IMC, "wrong", "correct")
    evaluate_attention_check(participant, 2, AttentionCheckResponse.CATCH_TRIAL, "wrong", "correct")

    participant.refresh_from_db()
    assert participant.excluded_inattentive is True
    assert participant.attention_checks_failed == 2


@pytest.mark.django_db
def test_one_failure_does_not_set_excluded():
    """Failing only one check leaves excluded_inattentive=False."""
    participant = ParticipantSessionFactory()

    evaluate_attention_check(participant, 1, AttentionCheckResponse.IMC, "wrong", "correct")

    participant.refresh_from_db()
    assert participant.excluded_inattentive is False
    assert participant.attention_checks_failed == 1
