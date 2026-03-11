import logging
from datetime import datetime

from django.utils import timezone

from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.models import Response
from mwhitestudy1.trials.models import Trial

logger = logging.getLogger(__name__)


def save_response(
    participant: ParticipantSession,
    trial: Trial,
    question: Question,
    value: str,
    stage: str,
    client_rt_ms: int | None = None,
) -> Response:
    """Validate and persist a single Response.

    Validates:
    - Question is active.
    - Question applies to the trial's condition (empty condition_applicability = all).
    - Stage matches the question's stage_location.

    Raises:
        ValueError: on any validation failure.
    """
    if not question.is_active:
        raise ValueError(f"Question {question.pk} is not active.")

    applicability = question.condition_applicability
    if applicability and trial.condition.name not in applicability:
        raise ValueError(
            f"Question {question.pk} does not apply to condition {trial.condition.name!r}."
        )

    if question.stage_location != stage:
        raise ValueError(
            f"Stage mismatch: question is for {question.stage_location!r}, "
            f"but stage argument is {stage!r}."
        )

    response = Response.objects.create(
        participant=participant,
        trial=trial,
        question=question,
        response_value=str(value),
        response_timestamp=timezone.now(),
        stage_location=stage,
        client_rt_ms=client_rt_ms,
    )
    logger.debug("Saved response pk=%d for trial pk=%d question pk=%d", response.pk, trial.pk, question.pk)
    return response
