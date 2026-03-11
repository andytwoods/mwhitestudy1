from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.models import Response
from mwhitestudy1.trials.models import Trial


def get_current_trial(participant) -> Trial | None:
    """Return the next incomplete trial for the participant.

    Practice trials (block_position=0) sort first.
    Returns None when all trials are complete.
    """
    completed_trial_ids = (
        Response.objects.filter(participant=participant)
        .values_list("trial_id", flat=True)
        .distinct()
    )

    # A trial is complete when it has responses for all its required stages.
    # We determine completeness by checking if a post_feedback or initial_judgement
    # response exists (depending on condition). Simplest: a trial is "done" when
    # get_current_stage returns "complete".
    all_trials = Trial.objects.filter(participant=participant).order_by(
        "-is_practice", "block_position", "trial_position"
    )

    for trial in all_trials:
        if get_current_stage(participant, trial) != "complete":
            return trial
    return None


def get_current_stage(participant, trial: Trial) -> str:
    """Return the current stage for a trial.

    Returns one of:
        'initial_judgement' — no responses yet
        'post_feedback'     — initial judgement done, awaiting post-feedback responses
        'complete'          — all required stages done

    For baseline trials, there is no feedback stage; completion is after initial judgement.
    """
    has_initial = Response.objects.filter(
        participant=participant,
        trial=trial,
        stage_location=Question.INITIAL_JUDGEMENT,
    ).exists()

    if not has_initial:
        return Question.INITIAL_JUDGEMENT

    is_baseline = trial.condition.name == "baseline"

    if is_baseline:
        # Baseline: complete after initial judgement
        return "complete"

    has_post_feedback = Response.objects.filter(
        participant=participant,
        trial=trial,
        stage_location=Question.POST_FEEDBACK,
    ).exists()

    if not has_post_feedback:
        return Question.POST_FEEDBACK

    return "complete"
