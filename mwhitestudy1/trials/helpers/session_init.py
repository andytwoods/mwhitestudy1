import logging
import random

from django.db import transaction

from mwhitestudy1.images.helpers.assignment import assign_images_to_participant
from mwhitestudy1.images.models import Image
from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.trials.models import FeedbackItem
from mwhitestudy1.trials.models import Trial

logger = logging.getLogger(__name__)


def _build_feedback_snapshot(trial_image, feedback_accuracy: str, condition, consensus: str) -> dict:
    """Build the Trial.feedback_presented JSON snapshot.

    Raises:
        ValueError: if no FeedbackItem records exist for a required agent/diagnosis combo.
    """
    required_diagnosis = (
        trial_image.ground_truth
        if feedback_accuracy == Trial.CORRECT
        else (Trial.MALIGNANT if trial_image.ground_truth == Trial.BENIGN else Trial.BENIGN)
    )

    agents = []
    for agent_def in condition.feedback_agents.all():
        pool = list(
            FeedbackItem.objects.filter(
                image=trial_image,
                agent_type=agent_def.agent_type,
                diagnosis=required_diagnosis,
            )
        )
        if not pool:
            raise ValueError(
                f"No FeedbackItems for image {trial_image.external_id!r}, "
                f"agent_type={agent_def.agent_type!r}, diagnosis={required_diagnosis!r}. "
                f"Run import_feedback_data first."
            )
        selected = random.choices(pool, k=agent_def.count)
        for item in selected:
            agents.append({
                "agent_type": item.agent_type,
                "label": agent_def.label,
                "diagnosis": item.diagnosis,
                "confidence": item.confidence,
                "feedback_item_id": item.pk,
            })

    return {
        "agents": agents,
        "consensus": consensus,
        "accuracy": feedback_accuracy,
    }


def _make_accuracy_sequence(n_trials: int, wrong_rate: float, is_feedback_condition: bool) -> list[str]:
    """Return a shuffled list of feedback_accuracy values for n_trials."""
    if not is_feedback_condition:
        return [Trial.NA] * n_trials
    n_wrong = round(n_trials * wrong_rate)
    sequence = [Trial.WRONG] * n_wrong + [Trial.CORRECT] * (n_trials - n_wrong)
    random.shuffle(sequence)
    return sequence


@transaction.atomic
def initialise_participant_session(participant: ParticipantSession) -> None:
    """Generate all Trial records for a participant.

    Steps:
    1. Randomise condition block order and store on the participant.
    2. Assign images via the assignment helper.
    3. For each condition block, create Trial records with feedback snapshots.
    4. Create practice Trial records.
    5. Mark one trial in block 2 as the catch trial (attention check 2).

    Raises:
        ValueError: propagated from image assignment or feedback snapshot
                    construction if the bank/pool is insufficient.
    """
    from mwhitestudy1.study.models import Condition

    study_config = participant.study.config_json
    wrong_rate: float = study_config.get("feedback_wrong_rate", 0.25)
    consensus: str = study_config.get("feedback_consensus", "unanimous")
    trials_per_condition: dict = study_config["trials_per_condition"]

    # 1. Randomise condition block order
    condition_names = list(trials_per_condition.keys())
    random.shuffle(condition_names)
    participant.condition_order = condition_names
    participant.save(update_fields=["condition_order"])

    # 2. Assign images
    image_map = assign_images_to_participant(participant, study_config)

    # Load condition objects
    condition_objs = {
        c.name: c
        for c in Condition.objects.prefetch_related("feedback_agents").filter(
            study=participant.study,
            name__in=condition_names,
        )
    }

    trials_to_create: list[Trial] = []

    # 3. Create real trials for each condition block
    for block_position, condition_name in enumerate(condition_names, start=1):
        condition = condition_objs[condition_name]
        images = image_map[condition_name]
        n_trials = len(images)
        is_feedback = condition_name != "baseline"

        accuracy_sequence = _make_accuracy_sequence(n_trials, wrong_rate, is_feedback)
        random.shuffle(images)  # randomise trial order within block

        for trial_position, (img, feedback_accuracy) in enumerate(
            zip(images, accuracy_sequence), start=1
        ):
            feedback_presented = None
            if is_feedback:
                feedback_presented = _build_feedback_snapshot(
                    img, feedback_accuracy, condition, consensus
                )

            trials_to_create.append(Trial(
                participant=participant,
                condition=condition,
                image=img,
                image_ground_truth=img.ground_truth,
                block_position=block_position,
                trial_position=trial_position,
                is_practice=False,
                is_catch_trial=False,
                feedback_presented=feedback_presented,
                feedback_accuracy=feedback_accuracy,
                feedback_consensus_level=consensus if is_feedback else "",
            ))

    Trial.objects.bulk_create(trials_to_create)

    # 5. Mark catch trial in block 2 (second block in randomised order)
    # Prefer a designated catch-trial image; fall back to any block-2 trial
    block2_trials = Trial.objects.filter(participant=participant, block_position=2).order_by("trial_position")
    catch_qs = block2_trials.filter(image__is_catch_trial=True)
    catch_trial = catch_qs.first() or block2_trials.first()
    if catch_trial:
        catch_trial.is_catch_trial = True
        catch_trial.save(update_fields=["is_catch_trial"])

    # 4. Create practice trials
    practice_images = list(Image.objects.filter(is_practice=True))
    practice_count = study_config.get("practice_trial_count", 5)
    practice_images = practice_images[:practice_count]

    practice_condition = condition_objs.get("baseline") or next(iter(condition_objs.values()))
    practice_trials = [
        Trial(
            participant=participant,
            condition=practice_condition,
            image=img,
            image_ground_truth=img.ground_truth,
            block_position=0,
            trial_position=pos,
            is_practice=True,
            is_catch_trial=False,
            feedback_presented=None,
            feedback_accuracy=Trial.NA,
            feedback_consensus_level="",
        )
        for pos, img in enumerate(practice_images, start=1)
    ]
    if practice_trials:
        Trial.objects.bulk_create(practice_trials)

    logger.info(
        "Initialised session for participant %s: %d real trials, %d practice trials",
        participant,
        len(trials_to_create),
        len(practice_trials),
    )
