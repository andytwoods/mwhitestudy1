import json
import logging
from pathlib import Path

from django.conf import settings

from mwhitestudy1.study.models import Study

logger = logging.getLogger(__name__)


def load_active_study_config() -> dict:
    """Read and parse the active study JSON config file.

    Raises:
        FileNotFoundError: if the config file does not exist.
        json.JSONDecodeError: if the file is not valid JSON.
    """
    config_path = Path(settings.BASE_DIR) / settings.ACTIVE_STUDY_CONFIG
    with open(config_path) as f:
        return json.load(f)


def get_or_create_active_study() -> Study:
    """Return the Study record for the active config, creating it if absent.

    The study is identified by its slug, which is set to the ``study_id``
    field from the JSON config. If the record already exists it is returned
    unchanged; the config_json snapshot is not updated on subsequent calls
    so that historical data integrity is preserved.
    """
    config = load_active_study_config()
    study_id = config["study_id"]
    study, created = Study.objects.get_or_create(
        slug=study_id,
        defaults={
            "name": study_id.replace("-", " ").title(),
            "config_json": config,
            "is_active": True,
            "consent_html": "",
            "consent_version": "1.0",
            "debrief_html": "",
            "debrief_version": "1.0",
        },
    )
    if created:
        logger.info("Created new Study record: %s", study)
    else:
        logger.info("Retrieved existing Study record: %s", study)
    return study
