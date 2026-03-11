import csv

import pytest
from django.core.management import call_command

from mwhitestudy1.images.tests.factories import ImageFactory
from mwhitestudy1.trials.models import FeedbackItem


def _write_csv(path, rows, header=("image_external_id", "agent_type", "diagnosis", "confidence", "source_label")):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.mark.django_db
def test_import_feedback_data_creates_records(tmp_path):
    """Valid CSV rows are imported as FeedbackItem records."""
    image = ImageFactory(external_id="img001", ground_truth="malignant")
    csv_file = tmp_path / "feedback.csv"
    _write_csv(csv_file, [("img001", "human", "malignant", "0.85", "Consultant Radiologist")])

    call_command("import_feedback_data", str(csv_file))

    assert FeedbackItem.objects.filter(image=image).count() == 1
    item = FeedbackItem.objects.get(image=image)
    assert item.agent_type == "human"
    assert item.diagnosis == "malignant"
    assert abs(item.confidence - 0.85) < 0.0001
    assert item.source_label == "Consultant Radiologist"


@pytest.mark.django_db
def test_import_feedback_data_skips_invalid_agent_type(tmp_path):
    """Row with invalid agent_type is skipped; no FeedbackItem created for it."""
    ImageFactory(external_id="img002")
    csv_file = tmp_path / "feedback.csv"
    _write_csv(csv_file, [("img002", "robot", "malignant", "0.8", "Some Label")])

    call_command("import_feedback_data", str(csv_file))

    assert FeedbackItem.objects.count() == 0


@pytest.mark.django_db
def test_import_feedback_data_skips_unknown_image(tmp_path):
    """Row referencing an external_id that doesn't exist is skipped."""
    csv_file = tmp_path / "feedback.csv"
    _write_csv(csv_file, [("no-such-image", "human", "malignant", "0.9", "Consultant Radiologist")])

    call_command("import_feedback_data", str(csv_file))

    assert FeedbackItem.objects.count() == 0


@pytest.mark.django_db
def test_import_feedback_data_skips_confidence_out_of_range(tmp_path):
    """Row with confidence > 1.0 is skipped."""
    ImageFactory(external_id="img003")
    csv_file = tmp_path / "feedback.csv"
    _write_csv(csv_file, [("img003", "human", "benign", "1.5", "Consultant Radiologist")])

    call_command("import_feedback_data", str(csv_file))

    assert FeedbackItem.objects.count() == 0


@pytest.mark.django_db
def test_import_feedback_data_partial_import(tmp_path):
    """Valid rows are imported even when other rows in the same file are invalid."""
    ImageFactory(external_id="img004", ground_truth="benign")
    csv_file = tmp_path / "feedback.csv"
    _write_csv(
        csv_file,
        [
            ("img004", "human", "benign", "0.7", "Consultant Radiologist"),
            ("no-such-image", "human", "malignant", "0.9", "Consultant Radiologist"),
        ],
    )

    call_command("import_feedback_data", str(csv_file))

    assert FeedbackItem.objects.count() == 1


def test_import_feedback_data_raises_for_missing_file(tmp_path):
    """Passing a non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        call_command("import_feedback_data", str(tmp_path / "nonexistent.csv"))
