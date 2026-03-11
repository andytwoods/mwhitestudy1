from django.db import models


class Image(models.Model):
    MALIGNANT = "malignant"
    BENIGN = "benign"
    GROUND_TRUTH_CHOICES = [
        (MALIGNANT, "Malignant"),
        (BENIGN, "Benign"),
    ]

    external_id = models.CharField(max_length=50, unique=True, db_index=True)
    ground_truth = models.CharField(max_length=50, choices=GROUND_TRUTH_CHOICES)
    image_file = models.ImageField(upload_to="images/")
    is_practice = models.BooleanField(default=False)
    is_catch_trial = models.BooleanField(default=False)
    source_dataset = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.external_id} ({self.ground_truth})"


class ImageAssignment(models.Model):
    image = models.ForeignKey(Image, on_delete=models.PROTECT, related_name="assignments")
    participant = models.ForeignKey(
        "participants.ParticipantSession",
        on_delete=models.CASCADE,
        related_name="image_assignments",
    )
    condition = models.ForeignKey(
        "study.Condition",
        on_delete=models.PROTECT,
        related_name="image_assignments",
    )

    class Meta:
        unique_together = [("image", "participant")]

    def __str__(self):
        return f"{self.image} → {self.participant} ({self.condition})"
