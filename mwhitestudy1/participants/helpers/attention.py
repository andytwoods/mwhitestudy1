import logging

from mwhitestudy1.participants.models import AttentionCheckResponse
from mwhitestudy1.participants.models import ParticipantSession

logger = logging.getLogger(__name__)

# Expected correct responses for each check type
_IMC_CORRECT_RESPONSE = "strongly_disagree"  # overridable per Question definition
_INFREQUENCY_CORRECT_RESPONSE = "never"


def evaluate_attention_check(
    participant: ParticipantSession,
    check_number: int,
    check_type: str,
    response_value: str,
    correct_response: str,
) -> bool:
    """Evaluate one attention check response, update participant state, and persist the record.

    Args:
        participant: The ParticipantSession being checked.
        check_number: 1, 2, or 3.
        check_type: One of AttentionCheckResponse.CHECK_TYPE_CHOICES values.
        response_value: The raw response submitted by the participant.
        correct_response: The expected correct answer for this check.

    Returns:
        True if the participant passed, False if they failed.
    """
    passed = response_value.strip().lower() == correct_response.strip().lower()

    AttentionCheckResponse.objects.create(
        participant=participant,
        check_number=check_number,
        check_type=check_type,
        response_value=response_value,
        passed=passed,
    )

    if not passed:
        participant.attention_checks_failed += 1
        participant.save(update_fields=["attention_checks_failed"])
        logger.info(
            "Participant %s failed attention check %d (total failed: %d)",
            participant,
            check_number,
            participant.attention_checks_failed,
        )

    _update_exclusion_flag(participant)
    return passed


def _update_exclusion_flag(participant: ParticipantSession) -> None:
    """Set excluded_inattentive=True if 2 or more checks have been failed."""
    if participant.attention_checks_failed >= 2 and not participant.excluded_inattentive:
        participant.excluded_inattentive = True
        participant.save(update_fields=["excluded_inattentive"])
        logger.info("Participant %s flagged as excluded_inattentive", participant)
