import csv
import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from mwhitestudy1.images.models import Image

logger = logging.getLogger(__name__)

_VALID_GROUND_TRUTHS = {Image.MALIGNANT, Image.BENIGN}
_BOOL_TRUE = {"true", "1", "yes"}


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in _BOOL_TRUE


class Command(BaseCommand):
    help = (
        "Import images from a source directory using a metadata CSV. "
        "Idempotent on external_id — existing records are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("source_dir", type=str, help="Directory containing image files")
        parser.add_argument("csv_path", type=str, help="Path to the metadata CSV file")

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"])
        csv_path = Path(options["csv_path"])

        if not source_dir.is_dir():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        dest_dir = Path(settings.MEDIA_ROOT) / "images"
        dest_dir.mkdir(parents=True, exist_ok=True)

        imported = 0
        skipped = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    external_id = row["external_id"].strip()
                    ground_truth = row["ground_truth"].strip()
                    is_practice = _parse_bool(row.get("is_practice", "false"))
                    is_catch_trial = _parse_bool(row.get("is_catch_trial", "false"))
                    source_dataset = row["source_dataset"].strip()

                    if ground_truth not in _VALID_GROUND_TRUTHS:
                        raise ValueError(
                            f"Invalid ground_truth: {ground_truth!r}. Must be one of {_VALID_GROUND_TRUTHS}"
                        )

                    if Image.objects.filter(external_id=external_id).exists():
                        logger.debug("Skipping existing image: %s", external_id)
                        skipped += 1
                        continue

                    # Find the source file by matching external_id against filenames
                    matches = list(source_dir.glob(f"{external_id}.*"))
                    if not matches:
                        raise ValueError(f"No file found in {source_dir} matching external_id: {external_id!r}")
                    if len(matches) > 1:
                        raise ValueError(
                            f"Multiple files found for external_id {external_id!r}: {[m.name for m in matches]}"
                        )

                    source_file = matches[0]
                    dest_file = dest_dir / source_file.name
                    shutil.copy2(source_file, dest_file)

                    # Store the relative path from MEDIA_ROOT
                    relative_path = dest_file.relative_to(Path(settings.MEDIA_ROOT))

                    Image.objects.create(
                        external_id=external_id,
                        ground_truth=ground_truth,
                        image_file=str(relative_path),
                        is_practice=is_practice,
                        is_catch_trial=is_catch_trial,
                        source_dataset=source_dataset,
                    )
                    imported += 1

                except (KeyError, ValueError) as exc:
                    logger.warning("Row %d skipped: %s", row_num, exc)
                    skipped += 1

        self.stdout.write(f"Imported: {imported}, Skipped: {skipped}")
