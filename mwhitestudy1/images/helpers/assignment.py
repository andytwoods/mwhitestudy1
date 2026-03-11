import logging
import random
from collections import Counter

from mwhitestudy1.images.models import Image
from mwhitestudy1.images.models import ImageAssignment

logger = logging.getLogger(__name__)


def _rank_sample(population: list, global_counts: Counter, k: int) -> list:
    """Sample k items from population, preferring lower-assigned images.

    Sorts candidates by their global assignment count (ascending), breaking
    ties with a random float. This guarantees that under-used images are
    selected first while still introducing randomness within equally-used
    groups, producing tight cross-participant balance (max-min typically ≤1).
    """
    if k == 0:
        return []
    ranked = sorted(population, key=lambda img: (global_counts[img.id], random.random()))
    return ranked[:k]


def assign_images_to_participant(participant, study_config: dict) -> dict:
    """Assign images from the bank to a participant for each condition.

    For each condition in the config, selects ``n_trials // 2`` malignant
    and ``n_trials - n_trials // 2`` benign images from the bank.
    Images are chosen using rank-based selection — candidates with the
    fewest existing assignments across all participants are preferred,
    with random tie-breaking.  No image is assigned twice to the same
    participant across any condition.

    ImageAssignment records are written in a single bulk_create after all
    conditions are resolved, so a validation failure leaves the DB clean.

    Args:
        participant: ParticipantSession instance.
        study_config: Parsed study JSON config dict.

    Returns:
        dict mapping condition name (str) → list[Image]

    Raises:
        ValueError: if the image bank has insufficient images to satisfy
                    the required allocation for any condition/ground-truth class.
    """
    from mwhitestudy1.study.models import Condition

    trials_per_condition: dict[str, int] = study_config["trials_per_condition"]

    conditions_qs = Condition.objects.filter(
        study=participant.study,
        name__in=list(trials_per_condition.keys()),
    )
    condition_map = {c.name: c for c in conditions_qs}

    already_assigned_ids: set[int] = set(
        ImageAssignment.objects.filter(participant=participant).values_list("image_id", flat=True)
    )

    global_counts: Counter = Counter(
        ImageAssignment.objects.values_list("image_id", flat=True)
    )

    result: dict[str, list[Image]] = {}
    assigned_this_session: set[int] = set()
    assignments_to_create: list[ImageAssignment] = []

    for condition_name, n_trials in trials_per_condition.items():
        n_malignant = n_trials // 2
        n_benign = n_trials - n_malignant

        condition_images: list[Image] = []
        excluded_ids = already_assigned_ids | assigned_this_session

        for ground_truth, n_needed in [
            (Image.MALIGNANT, n_malignant),
            (Image.BENIGN, n_benign),
        ]:
            candidates = list(
                Image.objects.filter(
                    ground_truth=ground_truth,
                    is_practice=False,
                ).exclude(id__in=excluded_ids)
            )

            if len(candidates) < n_needed:
                raise ValueError(
                    f"Insufficient {ground_truth} images for condition {condition_name!r}. "
                    f"Need {n_needed}, have {len(candidates)} available."
                )

            selected = _rank_sample(candidates, global_counts, n_needed)
            # Update the local counter so subsequent conditions see these picks
            global_counts.update(img.id for img in selected)

            condition_images.extend(selected)
            excluded_ids = excluded_ids | {img.id for img in selected}
            assigned_this_session.update(img.id for img in selected)

        result[condition_name] = condition_images
        condition_obj = condition_map[condition_name]
        assignments_to_create.extend(
            ImageAssignment(image=img, participant=participant, condition=condition_obj)
            for img in condition_images
        )

    ImageAssignment.objects.bulk_create(assignments_to_create)
    logger.info(
        "Assigned %d images to participant %s across %d conditions",
        len(assignments_to_create),
        participant,
        len(result),
    )

    return result
