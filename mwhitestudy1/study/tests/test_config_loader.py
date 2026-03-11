import json

import pytest
from django.test import override_settings

from mwhitestudy1.study.helpers.config_loader import get_or_create_active_study
from mwhitestudy1.study.helpers.config_loader import load_active_study_config
from mwhitestudy1.study.models import Study


# ---------------------------------------------------------------------------
# load_active_study_config
# ---------------------------------------------------------------------------


def test_load_active_study_config_returns_dict_with_required_keys(tmp_path, settings):
    """Valid JSON config file is parsed and returns a dict with expected keys."""
    config = {
        "study_id": "test-study",
        "trials_per_condition": {"baseline": 5},
        "feedback_wrong_rate": 0.25,
    }
    config_file = tmp_path / "study.json"
    config_file.write_text(json.dumps(config))
    settings.ACTIVE_STUDY_CONFIG = str(config_file)
    settings.BASE_DIR = tmp_path.parent  # file is at tmp_path / "study.json"

    result = load_active_study_config()

    assert isinstance(result, dict)
    assert "study_id" in result
    assert "trials_per_condition" in result
    assert "feedback_wrong_rate" in result


def test_load_active_study_config_raises_file_not_found(tmp_path, settings):
    """Non-existent config path raises FileNotFoundError."""
    settings.ACTIVE_STUDY_CONFIG = str(tmp_path / "nonexistent.json")
    settings.BASE_DIR = ""  # path is already absolute via ACTIVE_STUDY_CONFIG

    with pytest.raises(FileNotFoundError):
        load_active_study_config()


def test_load_active_study_config_raises_json_decode_error(tmp_path, settings):
    """Malformed JSON raises json.JSONDecodeError."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ not valid json }")
    settings.ACTIVE_STUDY_CONFIG = str(bad_file)
    settings.BASE_DIR = ""

    with pytest.raises(json.JSONDecodeError):
        load_active_study_config()


@pytest.mark.django_db
def test_get_or_create_active_study_is_idempotent(tmp_path, settings):
    """Calling get_or_create_active_study twice returns the same Study; no duplicate created."""
    config = {
        "study_id": "idempotent-study",
        "trials_per_condition": {"baseline": 5},
        "feedback_wrong_rate": 0.25,
        "feedback_consensus": "unanimous",
        "feedback_agents": {},
        "practice_trial_count": 5,
        "prolific_completion_code": "CODE",
        "payment_gbp": 12.0,
    }
    config_file = tmp_path / "study.json"
    config_file.write_text(json.dumps(config))
    settings.ACTIVE_STUDY_CONFIG = str(config_file)
    settings.BASE_DIR = ""

    get_or_create_active_study()
    get_or_create_active_study()

    assert Study.objects.filter(slug="idempotent-study").count() == 1
