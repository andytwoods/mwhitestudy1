import pytest

from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory
from mwhitestudy1.study.tests.factories import ConditionFactory
from mwhitestudy1.study.tests.factories import StudyFactory
from mwhitestudy1.trials.helpers.response_save import save_response
from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.models import Response
from mwhitestudy1.trials.tests.factories import QuestionFactory
from mwhitestudy1.trials.tests.factories import TrialFactory


@pytest.mark.django_db
def test_save_response_creates_record_with_timestamp():
    """Valid inputs create a Response with a non-null timestamp."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition)
    question = QuestionFactory(study=study, stage_location=Question.INITIAL_JUDGEMENT)

    resp = save_response(participant, trial, question, "malignant", Question.INITIAL_JUDGEMENT)

    assert Response.objects.count() == 1
    assert resp.response_timestamp is not None


@pytest.mark.django_db
def test_save_response_inactive_question_raises():
    """Saving a response to an inactive question raises ValueError."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition)
    question = QuestionFactory(study=study, stage_location=Question.INITIAL_JUDGEMENT, is_active=False)

    with pytest.raises(ValueError):
        save_response(participant, trial, question, "malignant", Question.INITIAL_JUDGEMENT)

    assert Response.objects.count() == 0


@pytest.mark.django_db
def test_save_response_wrong_condition_raises():
    """Question not applicable to trial's condition raises ValueError."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition)
    question = QuestionFactory(
        study=study,
        stage_location=Question.POST_FEEDBACK,
        condition_applicability=["human", "human_ai", "ai"],
    )

    with pytest.raises(ValueError):
        save_response(participant, trial, question, "5", Question.POST_FEEDBACK)

    assert Response.objects.count() == 0
