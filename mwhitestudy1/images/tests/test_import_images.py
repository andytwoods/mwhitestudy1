import csv
from pathlib import Path

import pytest
from django.core.management import call_command
from PIL import Image as PilImage

from mwhitestudy1.images.models import Image


def _make_image_file(directory: Path, name: str) -> Path:
    """Create a tiny valid PNG file in directory."""
    path = directory / name
    img = PilImage.new("RGB", (10, 10), color=(128, 128, 128))
    img.save(path)
    return path


def _write_csv(path: Path, rows: list[tuple], header=None):
    if header is None:
        header = ("external_id", "ground_truth", "is_practice", "is_catch_trial", "source_dataset")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.mark.django_db
def test_import_images_creates_records(tmp_path):
    """Valid CSV + matching image files creates Image records."""
    _make_image_file(tmp_path, "img001.png")
    _write_csv(tmp_path / "meta.csv", [("img001", "malignant", "false", "false", "dataset_a")])

    call_command("import_images", str(tmp_path), str(tmp_path / "meta.csv"))

    assert Image.objects.count() == 1
    img = Image.objects.get(external_id="img001")
    assert img.ground_truth == "malignant"
    assert img.is_practice is False
    assert img.source_dataset == "dataset_a"


@pytest.mark.django_db
def test_import_images_is_idempotent(tmp_path):
    """Running import_images twice with the same CSV does not create duplicate records."""
    _make_image_file(tmp_path, "img002.png")
    _write_csv(tmp_path / "meta.csv", [("img002", "benign", "false", "false", "dataset_a")])

    call_command("import_images", str(tmp_path), str(tmp_path / "meta.csv"))
    call_command("import_images", str(tmp_path), str(tmp_path / "meta.csv"))

    assert Image.objects.filter(external_id="img002").count() == 1


@pytest.mark.django_db
def test_import_images_skips_invalid_ground_truth(tmp_path):
    """Row with invalid ground_truth is skipped; no Image created."""
    _make_image_file(tmp_path, "img003.png")
    _write_csv(tmp_path / "meta.csv", [("img003", "suspicious", "false", "false", "dataset_a")])

    call_command("import_images", str(tmp_path), str(tmp_path / "meta.csv"))

    assert Image.objects.filter(external_id="img003").exists() is False


def test_import_images_raises_for_missing_directory(tmp_path):
    """Non-existent source directory raises FileNotFoundError."""
    _write_csv(tmp_path / "meta.csv", [])
    with pytest.raises(FileNotFoundError):
        call_command("import_images", str(tmp_path / "no_such_dir"), str(tmp_path / "meta.csv"))


def test_import_images_raises_for_missing_csv(tmp_path):
    """Non-existent CSV raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        call_command("import_images", str(tmp_path), str(tmp_path / "no_such.csv"))
