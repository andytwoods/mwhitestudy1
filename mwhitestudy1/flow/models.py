import uuid
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

class Participant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"Participant {self.id}"

class Progress(TimeStampedModel):
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE, related_name="progress")
    current_screen_key = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.participant.id} at {self.current_screen_key}"

class Response(TimeStampedModel):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="responses")
    screen_key = models.CharField(max_length=255)
    question_id = models.CharField(max_length=255)
    value = models.JSONField()

    def __str__(self):
        return f"{self.participant.id} - {self.screen_key} - {self.question_id}"

class ScreenEvent(models.Model):
    EVENT_TYPES = (
        ("render", "Render"),
        ("submit", "Submit"),
        ("advance", "Advance"),
    )
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="events")
    screen_key = models.CharField(max_length=255)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.participant.id} - {self.event_type} - {self.screen_key}"
