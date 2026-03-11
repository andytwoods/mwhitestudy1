import pytest

from mwhitestudy1.images.tests.factories import ImageFactory
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory
from mwhitestudy1.study.tests.factories import ConditionFactory
from mwhitestudy1.study.tests.factories import StudyFactory
from mwhitestudy1.trials.helpers.trial_state import get_current_stage
from mwhitestudy1.trials.helpers.trial_state import get_current_trial
from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.tests.factories import QuestionFactory
from mwhitestudy1.trials.tests.factories import ResponseFactory
from mwhitestudy1.trials.tests.factories import TrialFactory


@pytest.mark.django_db
def test_get_current_trial_returns_first_incomplete():
    """Returns the trial with lowest block/trial position that has no responses."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    t1 = TrialFactory(participant=participant, condition=condition, block_position=1, trial_position=1)
    TrialFactory(participant=participant, condition=condition, block_position=1, trial_position=2)

    result = get_current_trial(participant)
    assert result.pk == t1.pk


@pytest.mark.django_db
def test_get_current_trial_returns_none_when_all_done():
    """Returns None when all trials are complete."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition, block_position=1, trial_position=1)
    q = QuestionFactory(study=study, stage_location=Question.INITIAL_JUDGEMENT)
    ResponseFactory(participant=participant, trial=trial, question=q, stage_location=Question.INITIAL_JUDGEMENT)

    assert get_current_trial(participant) is None


@pytest.mark.django_db
def test_get_current_stage_no_responses_returns_initial():
    """Trial with no responses returns 'initial_judgement'."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition)

    assert get_current_stage(participant, trial) == Question.INITIAL_JUDGEMENT


@pytest.mark.django_db
def test_get_current_stage_after_initial_baseline_is_complete():
    """Baseline trial is complete after initial judgement."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="baseline")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition)
    q = QuestionFactory(study=study, stage_location=Question.INITIAL_JUDGEMENT)
    ResponseFactory(participant=participant, trial=trial, question=q, stage_location=Question.INITIAL_JUDGEMENT)

    assert get_current_stage(participant, trial) == "complete"


@pytest.mark.django_db
def test_get_current_stage_after_initial_non_baseline_returns_post_feedback():
    """Non-baseline trial returns 'post_feedback' after initial judgement."""
    study = StudyFactory()
    condition = ConditionFactory(study=study, name="human")
    participant = ParticipantSessionFactory(study=study)
    trial = TrialFactory(participant=participant, condition=condition)
    q = QuestionFactory(study=study, stage_location=Question.INITIAL_JUDGEMENT)
    ResponseFactory(participant=participant, trial=trial, question=q, stage_location=Question.INITIAL_JUDGEMENT)

    assert get_current_stage(participant, trial) == Question.POST_FEEDBACK
