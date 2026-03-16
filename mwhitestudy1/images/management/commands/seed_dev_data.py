"""Management command: seed placeholder images and feedback items for local development.

Creates the minimum number of Image and FeedbackItem records needed to run through
the full participant flow without real image files or real feedback data.

Safe to re-run — existing records (matched by external_id) are skipped.

Usage:
    python manage.py seed_dev_data --settings=config.settings.local
"""

from django.core.management.base import BaseCommand

from mwhitestudy1.images.models import Image
from mwhitestudy1.trials.models import FeedbackItem


# Study config expects: 4 conditions × 5 trials each = 20 real trials.
# Per condition: n_trials//2 malignant (2) + n_trials - n_trials//2 benign (3).
# Across 4 conditions with no reuse: 4×2 = 8 malignant, 4×3 = 12 benign.
_N_MALIGNANT = 8
_N_BENIGN = 12
_N_PRACTICE = 5

# Each real image needs FeedbackItems for both agent types and both diagnoses
# so that the session initialiser can build correct AND wrong feedback snapshots.
_AGENT_TYPES = [FeedbackItem.HUMAN, FeedbackItem.AI]
_DIAGNOSES = [FeedbackItem.MALIGNANT, FeedbackItem.BENIGN]


class Command(BaseCommand):
    help = (
        "Seed placeholder images and feedback items for local development. "
        "Idempotent — existing records are skipped."
    )

    def handle(self, *args, **options):
        images_created = 0
        feedback_created = 0

        # --- Practice images ---
        for i in range(1, _N_PRACTICE + 1):
            external_id = f"practice_{i:03d}"
            ground_truth = Image.MALIGNANT if i % 2 == 1 else Image.BENIGN
            if not Image.objects.filter(external_id=external_id).exists():
                Image.objects.create(
                    external_id=external_id,
                    ground_truth=ground_truth,
                    image_file="images/placeholder.jpg",
                    is_practice=True,
                    is_catch_trial=False,
                    source_dataset="dev_seed",
                )
                images_created += 1

        # --- Real malignant images ---
        for i in range(1, _N_MALIGNANT + 1):
            external_id = f"mal_{i:03d}"
            if not Image.objects.filter(external_id=external_id).exists():
                img = Image.objects.create(
                    external_id=external_id,
                    ground_truth=Image.MALIGNANT,
                    image_file="images/placeholder.jpg",
                    is_practice=False,
                    is_catch_trial=(i == 1),  # mark first as catch-trial candidate
                    source_dataset="dev_seed",
                )
                images_created += 1
                feedback_created += _create_feedback_items(img)

        # --- Real benign images ---
        for i in range(1, _N_BENIGN + 1):
            external_id = f"ben_{i:03d}"
            if not Image.objects.filter(external_id=external_id).exists():
                img = Image.objects.create(
                    external_id=external_id,
                    ground_truth=Image.BENIGN,
                    image_file="images/placeholder.jpg",
                    is_practice=False,
                    is_catch_trial=False,
                    source_dataset="dev_seed",
                )
                images_created += 1
                feedback_created += _create_feedback_items(img)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Images created: {images_created}, FeedbackItems created: {feedback_created}"
            )
        )


def _create_feedback_items(image: Image) -> int:
    """Create one FeedbackItem per (agent_type, diagnosis) combination for *image*."""
    created = 0
    for agent_type in _AGENT_TYPES:
        for diagnosis in _DIAGNOSES:
            confidence = 0.85 if diagnosis == image.ground_truth else 0.30
            FeedbackItem.objects.create(
                image=image,
                agent_type=agent_type,
                diagnosis=diagnosis,
                confidence=confidence,
                source_label=f"Dev {agent_type.upper()} seed",
            )
            created += 1
    return created
