"""Management command to create placeholder images for development/testing.

Generates simple PNG files with descriptive text labels and creates
corresponding Image database records. Idempotent on external_id.
"""
import io
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from mwhitestudy1.images.models import Image

_COLOURS = {
    Image.MALIGNANT: (220, 80, 80),
    Image.BENIGN: (80, 160, 220),
}
_BG = (240, 240, 240)
_WIDTH, _HEIGHT = 400, 400


def _make_placeholder_image(label: str, ground_truth: str) -> bytes:
    from PIL import Image as PILImage, ImageDraw

    img = PILImage.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(img)

    # Coloured border
    colour = _COLOURS[ground_truth]
    border = 20
    draw.rectangle([border, border, _WIDTH - border, _HEIGHT - border], outline=colour, width=6)

    # Ground truth band
    draw.rectangle([0, _HEIGHT // 2 - 30, _WIDTH, _HEIGHT // 2 + 30], fill=colour)
    draw.text((_WIDTH // 2, _HEIGHT // 2), ground_truth.upper(), fill=(255, 255, 255), anchor="mm")

    # Label text — split onto two lines if needed
    parts = label.split(" placeholder ")
    line1 = parts[0] if parts else label
    line2 = f"placeholder {parts[1]}" if len(parts) > 1 else ""
    draw.text((_WIDTH // 2, _HEIGHT // 2 - 80), line1, fill=(60, 60, 60), anchor="mm")
    if line2:
        draw.text((_WIDTH // 2, _HEIGHT // 2 - 50), line2, fill=(60, 60, 60), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class Command(BaseCommand):
    help = (
        "Create placeholder images for development/testing. "
        "Generates simple labelled PNG files and Image DB records. "
        "Idempotent — existing external_ids are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of placeholder images to create per ground_truth class (default: 20)",
        )
        parser.add_argument(
            "--practice-count",
            type=int,
            default=5,
            help="Number of practice placeholder images to create (default: 5)",
        )

    def handle(self, *args, **options):
        dest_dir = Path(settings.MEDIA_ROOT) / "images"
        dest_dir.mkdir(parents=True, exist_ok=True)

        count = options["count"]
        practice_count = options["practice_count"]
        created = 0
        skipped = 0

        specs = (
            [(Image.MALIGNANT, i, False) for i in range(1, count + 1)]
            + [(Image.BENIGN, i, False) for i in range(1, count + 1)]
            + [(Image.MALIGNANT, i, True) for i in range(1, practice_count + 1)]
        )

        for ground_truth, idx, is_practice in specs:
            prefix = "practice" if is_practice else ground_truth
            external_id = f"placeholder_{prefix}_{idx:03d}"

            if Image.objects.filter(external_id=external_id).exists():
                skipped += 1
                continue

            label = f"{prefix} placeholder {idx}"
            png_bytes = _make_placeholder_image(label, ground_truth)

            filename = f"{external_id}.png"
            dest_file = dest_dir / filename
            dest_file.write_bytes(png_bytes)

            relative_path = dest_file.relative_to(Path(settings.MEDIA_ROOT))
            Image.objects.create(
                external_id=external_id,
                ground_truth=ground_truth,
                image_file=str(relative_path),
                is_practice=is_practice,
                is_catch_trial=False,
                source_dataset="placeholder",
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created: {created}, Skipped (already exist): {skipped}")
        )
