from collections import Counter

import pytest

from mwhitestudy1.images.helpers.assignment import assign_images_to_participant
from mwhitestudy1.images.models import Image
from mwhitestudy1.images.models import ImageAssignment
from mwhitestudy1.images.tests.factories import ImageFactory
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory
from mwhitestudy1.study.tests.factories import ConditionFactory
from mwhitestudy1.study.tests.factories import StudyFactory


_CONFIG_4_PER_CONDITION = {
    "trials_per_condition": {"baseline": 4, "human": 4, "human_ai": 4, "ai": 4},
}


def _make_bank(study, n_malignant: int, n_benign: int):
    """Create Image records and all four Conditions for the given study."""
    for condition_name in ["baseline", "human", "human_ai", "ai"]:
        ConditionFactory(study=study, name=condition_name)
    for i in range(n_malignant):
        ImageFactory(external_id=f"mal_{i:04d}", ground_truth=Image.MALIGNANT, is_practice=False)
    for i in range(n_benign):
        ImageFactory(external_id=f"ben_{i:04d}", ground_truth=Image.BENIGN, is_practice=False)


@pytest.mark.django_db
def test_no_image_assigned_to_more_than_one_condition_per_participant():
    """Each image appears at most once across all conditions for a single participant."""
    study = StudyFactory()
    _make_bank(study, n_malignant=20, n_benign=20)
    participant = ParticipantSessionFactory(study=study)

    result = assign_images_to_participant(participant, _CONFIG_4_PER_CONDITION)

    all_ids = [img.id for imgs in result.values() for img in imgs]
    assert len(all_ids) == len(set(all_ids)), "Duplicate image assigned across conditions"


@pytest.mark.django_db
def test_each_condition_receives_equal_malignant_and_benign():
    """With 4 trials per condition each condition gets exactly 2 malignant and 2 benign."""
    study = StudyFactory()
    _make_bank(study, n_malignant=20, n_benign=20)
    participant = ParticipantSessionFactory(study=study)

    result = assign_images_to_participant(participant, _CONFIG_4_PER_CONDITION)

    for condition_name, images in result.items():
        malignant_count = sum(1 for img in images if img.ground_truth == Image.MALIGNANT)
        benign_count = sum(1 for img in images if img.ground_truth == Image.BENIGN)
        assert malignant_count == 2, f"Condition {condition_name}: expected 2 malignant, got {malignant_count}"
        assert benign_count == 2, f"Condition {condition_name}: expected 2 benign, got {benign_count}"


@pytest.mark.django_db
def test_assignment_balance_across_participants():
    """Across 10 participants, no image's assignment count diverges by more than 2."""
    study = StudyFactory()
    # 16 images per class, 4 conditions × 2 per class = 8 per class per participant
    # → each image should appear ~5 times across 10 participants
    _make_bank(study, n_malignant=16, n_benign=16)

    for _ in range(10):
        participant = ParticipantSessionFactory(study=study)
        assign_images_to_participant(participant, _CONFIG_4_PER_CONDITION)

    counts = Counter(ImageAssignment.objects.values_list("image_id", flat=True))
    values = list(counts.values())
    assert max(values) - min(values) <= 2, (
        f"Assignment imbalance too large: max={max(values)}, min={min(values)}"
    )


@pytest.mark.django_db
def test_assign_images_raises_when_bank_insufficient():
    """ValueError is raised if there are not enough images to satisfy the allocation."""
    study = StudyFactory()
    # Only 1 malignant image — need 2 per condition
    _make_bank(study, n_malignant=1, n_benign=20)
    participant = ParticipantSessionFactory(study=study)

    with pytest.raises(ValueError, match="Insufficient malignant"):
        assign_images_to_participant(participant, _CONFIG_4_PER_CONDITION)


@pytest.mark.django_db
def test_assignment_writes_image_assignment_records():
    """ImageAssignment records are created for every assigned image."""
    study = StudyFactory()
    _make_bank(study, n_malignant=20, n_benign=20)
    participant = ParticipantSessionFactory(study=study)

    assign_images_to_participant(participant, _CONFIG_4_PER_CONDITION)

    total_trials = sum(_CONFIG_4_PER_CONDITION["trials_per_condition"].values())
    assert ImageAssignment.objects.filter(participant=participant).count() == total_trials
