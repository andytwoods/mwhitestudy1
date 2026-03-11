import csv
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from mwhitestudy1.images.models import Image
from mwhitestudy1.trials.models import FeedbackItem

logger = logging.getLogger(__name__)

_VALID_AGENT_TYPES = {FeedbackItem.HUMAN, FeedbackItem.AI}
_VALID_DIAGNOSES = {FeedbackItem.MALIGNANT, FeedbackItem.BENIGN}


class Command(BaseCommand):
    help = "Import feedback data from a CSV file into FeedbackItem records."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        imported = 0
        skipped = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    image_external_id = row["image_external_id"].strip()
                    agent_type = row["agent_type"].strip()
                    diagnosis = row["diagnosis"].strip()
                    confidence_str = row["confidence"].strip()
                    source_label = row["source_label"].strip()

                    if agent_type not in _VALID_AGENT_TYPES:
                        raise ValueError(f"Invalid agent_type: {agent_type!r}. Must be one of {_VALID_AGENT_TYPES}")
                    if diagnosis not in _VALID_DIAGNOSES:
                        raise ValueError(f"Invalid diagnosis: {diagnosis!r}. Must be one of {_VALID_DIAGNOSES}")

                    confidence = float(confidence_str)
                    if not 0.0 <= confidence <= 1.0:
                        raise ValueError(f"confidence out of range [0.0, 1.0]: {confidence}")

                    if len(source_label) > 100:
                        raise ValueError(f"source_label exceeds 100 chars ({len(source_label)})")

                    try:
                        image = Image.objects.get(external_id=image_external_id)
                    except Image.DoesNotExist:
                        raise ValueError(f"Image not found with external_id: {image_external_id!r}")

                    FeedbackItem.objects.create(
                        image=image,
                        agent_type=agent_type,
                        diagnosis=diagnosis,
                        confidence=confidence,
                        source_label=source_label,
                    )
                    imported += 1

                except (KeyError, ValueError) as exc:
                    logger.warning("Row %d skipped: %s", row_num, exc)
                    skipped += 1

        self.stdout.write(f"Imported: {imported}, Skipped: {skipped}")
