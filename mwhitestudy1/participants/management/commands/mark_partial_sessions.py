from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from mwhitestudy1.participants.models import ParticipantSession

TIMEOUT_HOURS = 2


class Command(BaseCommand):
    help = "Mark in_progress sessions older than 2 hours as partial (run nightly)."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=TIMEOUT_HOURS)
        updated = ParticipantSession.objects.filter(
            completion_status=ParticipantSession.IN_PROGRESS,
            entry_timestamp__lt=cutoff,
        ).update(completion_status=ParticipantSession.PARTIAL)
        self.stdout.write(f"Marked {updated} sessions as partial.")
