import json

import pytest
from django.core.management import call_command

from mwhitestudy1.study.models import Condition
from mwhitestudy1.study.models import FeedbackAgentDefinition
from mwhitestudy1.study.models import Study
from mwhitestudy1.trials.models import Question


def _write_config(path, config):
    path.write_text(json.dumps(config))


VALID_CONFIG = {
    "study_id": "bootstrap-test",
    "payment_gbp": 12.0,
    "practice_trial_count": 5,
    "prolific_completion_code": "CODE",
    "trials_per_condition": {"baseline": 5, "human": 5, "human_ai": 5, "ai": 5},
    "feedback_wrong_rate": 0.25,
    "feedback_consensus": "unanimous",
    "feedback_agents": {
        "human": [{"type": "human", "label": "Consultant Radiologist", "count": 3}],
        "human_ai": [
            {"type": "human", "label": "Consultant Radiologist", "count": 3},
            {"type": "ai", "label": "AI Diagnostic System", "count": 1},
        ],
        "ai": [{"type": "ai", "label": "AI Diagnostic System", "count": 1}],
    },
}


@pytest.mark.django_db
def test_bootstrap_study_creates_expected_records(tmp_path, settings):
    """Running bootstrap_study once creates Study, all Conditions, and FeedbackAgentDefinitions."""
    cfg_file = tmp_path / "s.json"
    _write_config(cfg_file, VALID_CONFIG)
    settings.ACTIVE_STUDY_CONFIG = str(cfg_file)
    settings.BASE_DIR = ""

    call_command("bootstrap_study")

    assert Study.objects.filter(slug="bootstrap-test").count() == 1
    study = Study.objects.get(slug="bootstrap-test")
    assert Condition.objects.filter(study=study).count() == 4
    assert FeedbackAgentDefinition.objects.filter(condition__study=study).count() == 4
    assert Question.objects.filter(study=study).count() == 6


@pytest.mark.django_db
def test_bootstrap_study_is_idempotent(tmp_path, settings):
    """Running bootstrap_study twice produces the same counts as running it once."""
    cfg_file = tmp_path / "s.json"
    _write_config(cfg_file, VALID_CONFIG)
    settings.ACTIVE_STUDY_CONFIG = str(cfg_file)
    settings.BASE_DIR = ""

    call_command("bootstrap_study")
    call_command("bootstrap_study")

    study = Study.objects.get(slug="bootstrap-test")
    assert Study.objects.filter(slug="bootstrap-test").count() == 1
    assert Condition.objects.filter(study=study).count() == 4
    assert FeedbackAgentDefinition.objects.filter(condition__study=study).count() == 4
    assert Question.objects.filter(study=study).count() == 6


@pytest.mark.django_db
def test_bootstrap_study_raises_on_missing_required_key(tmp_path, settings):
    """Config missing trials_per_condition raises KeyError before writing to DB."""
    bad_config = {k: v for k, v in VALID_CONFIG.items() if k != "trials_per_condition"}
    cfg_file = tmp_path / "s.json"
    _write_config(cfg_file, bad_config)
    settings.ACTIVE_STUDY_CONFIG = str(cfg_file)
    settings.BASE_DIR = ""

    with pytest.raises(KeyError):
        call_command("bootstrap_study")

    assert Study.objects.count() == 0
