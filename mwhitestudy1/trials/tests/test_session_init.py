from collections import Counter

import pytest

from mwhitestudy1.images.models import Image
from mwhitestudy1.images.tests.factories import ImageFactory
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory
from mwhitestudy1.study.tests.factories import ConditionFactory
from mwhitestudy1.study.tests.factories import FeedbackAgentDefinitionFactory
from mwhitestudy1.study.tests.factories import StudyFactory
from mwhitestudy1.trials.helpers.session_init import initialise_participant_session
from mwhitestudy1.trials.models import FeedbackItem
from mwhitestudy1.trials.models import Trial
from mwhitestudy1.trials.tests.factories import FeedbackItemFactory


_CONFIG = {
    "trials_per_condition": {"baseline": 4, "human": 4, "human_ai": 4, "ai": 4},
    "feedback_wrong_rate": 0.25,
    "feedback_consensus": "unanimous",
    "practice_trial_count": 2,
    "feedback_agents": {
        "human": [{"type": "human", "label": "Consultant Radiologist", "count": 1}],
        "human_ai": [
            {"type": "human", "label": "Consultant Radiologist", "count": 1},
            {"type": "ai", "label": "AI Diagnostic System", "count": 1},
        ],
        "ai": [{"type": "ai", "label": "AI Diagnostic System", "count": 1}],
    },
}


def _setup_study(config=None):
    cfg = config or _CONFIG
    study = StudyFactory(config_json=cfg)
    for name in cfg["trials_per_condition"]:
        cond = ConditionFactory(study=study, name=name)
        for agent_def in cfg.get("feedback_agents", {}).get(name, []):
            FeedbackAgentDefinitionFactory(
                condition=cond,
                agent_type=agent_def["type"],
                label=agent_def["label"],
                count=agent_def["count"],
            )
    return study


def _make_bank(n_mal=16, n_ben=16, with_feedback=True):
    images = []
    for i in range(n_mal):
        img = ImageFactory(external_id=f"mal_{i:04d}", ground_truth=Image.MALIGNANT, is_practice=False)
        if with_feedback:
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.HUMAN, diagnosis=Image.MALIGNANT)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.HUMAN, diagnosis=Image.BENIGN)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.AI, diagnosis=Image.MALIGNANT)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.AI, diagnosis=Image.BENIGN)
        images.append(img)
    for i in range(n_ben):
        img = ImageFactory(external_id=f"ben_{i:04d}", ground_truth=Image.BENIGN, is_practice=False)
        if with_feedback:
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.HUMAN, diagnosis=Image.MALIGNANT)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.HUMAN, diagnosis=Image.BENIGN)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.AI, diagnosis=Image.MALIGNANT)
            FeedbackItemFactory(image=img, agent_type=FeedbackItem.AI, diagnosis=Image.BENIGN)
        images.append(img)
    return images


@pytest.mark.django_db
def test_correct_number_of_trials_created():
    """20 non-practice Trials created (4 conditions × 4 trials)."""
    study = _setup_study()
    _make_bank()
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)

    assert Trial.objects.filter(participant=participant, is_practice=False).count() == 16


@pytest.mark.django_db
def test_block_positions_correct():
    """block_position values 1-4 each appear exactly 4 times."""
    study = _setup_study()
    _make_bank()
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)

    positions = list(
        Trial.objects.filter(participant=participant, is_practice=False)
        .values_list("block_position", flat=True)
    )
    assert Counter(positions) == {1: 4, 2: 4, 3: 4, 4: 4}


@pytest.mark.django_db
def test_trial_positions_within_block():
    """trial_position within each block is 1-4 with no gaps or repeats."""
    study = _setup_study()
    _make_bank()
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)

    for block in range(1, 5):
        positions = sorted(
            Trial.objects.filter(participant=participant, block_position=block)
            .values_list("trial_position", flat=True)
        )
        assert positions == [1, 2, 3, 4]


@pytest.mark.django_db
def test_condition_order_stored_on_participant():
    """condition_order contains all 4 condition names exactly once."""
    study = _setup_study()
    _make_bank()
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)
    participant.refresh_from_db()

    assert sorted(participant.condition_order) == sorted(["baseline", "human", "human_ai", "ai"])


@pytest.mark.django_db
def test_feedback_accuracy_wrong_rate():
    """Wrong-feedback rate across 20 participants is between 0.20 and 0.30."""
    study = _setup_study()
    _make_bank(n_mal=40, n_ben=40)

    wrong_count = 0
    total_feedback = 0
    for _ in range(20):
        participant = ParticipantSessionFactory(study=study)
        initialise_participant_session(participant)
        trials = Trial.objects.filter(participant=participant, is_practice=False).exclude(
            feedback_accuracy=Trial.NA
        )
        wrong_count += trials.filter(feedback_accuracy=Trial.WRONG).count()
        total_feedback += trials.count()

    wrong_rate = wrong_count / total_feedback
    assert 0.20 <= wrong_rate <= 0.30, f"Wrong rate {wrong_rate:.2f} outside expected range"


@pytest.mark.django_db
def test_practice_trials_created():
    """Practice trials (block_position=0) are created up to practice_trial_count."""
    study = _setup_study()
    _make_bank()
    ImageFactory(external_id="prac_0001", ground_truth=Image.MALIGNANT, is_practice=True)
    ImageFactory(external_id="prac_0002", ground_truth=Image.BENIGN, is_practice=True)
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)

    practice = Trial.objects.filter(participant=participant, is_practice=True)
    assert practice.count() == 2
    assert all(t.block_position == 0 for t in practice)


@pytest.mark.django_db
def test_catch_trial_flagged_in_block_2():
    """Exactly one trial in block 2 is flagged as is_catch_trial=True."""
    study = _setup_study()
    _make_bank()
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)

    catch_trials = Trial.objects.filter(participant=participant, is_catch_trial=True)
    assert catch_trials.count() == 1
    assert catch_trials.first().block_position == 2


@pytest.mark.django_db
def test_baseline_trials_have_no_feedback():
    """All baseline trials have feedback_presented=None and feedback_accuracy='na'."""
    study = _setup_study()
    _make_bank()
    participant = ParticipantSessionFactory(study=study)

    initialise_participant_session(participant)
    participant.refresh_from_db()

    # Find baseline block position
    baseline_pos = participant.condition_order.index("baseline") + 1
    baseline_trials = Trial.objects.filter(participant=participant, block_position=baseline_pos)

    for trial in baseline_trials:
        assert trial.feedback_presented is None
        assert trial.feedback_accuracy == Trial.NA


@pytest.mark.django_db
def test_no_feedback_items_raises():
    """ValueError raised before creating any Trials if feedback pool is empty."""
    study = _setup_study()
    _make_bank(with_feedback=False)
    participant = ParticipantSessionFactory(study=study)

    with pytest.raises(ValueError, match="No FeedbackItems"):
        initialise_participant_session(participant)

    assert Trial.objects.filter(participant=participant).count() == 0
