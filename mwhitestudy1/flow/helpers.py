from .models import Participant, Progress
from .study import get_first_screen_key

def get_or_create_participant(request):
    participant_id = request.session.get("participant_id")
    participant = None

    if participant_id:
        try:
            participant = Participant.objects.get(id=participant_id)
        except Participant.DoesNotExist:
            participant = None

    if not participant:
        participant = Participant.objects.create(
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ip_address=request.META.get("REMOTE_ADDR", "")
        )
        request.session["participant_id"] = str(participant.id)

    return participant

def get_or_create_progress(participant):
    progress, created = Progress.objects.get_or_create(
        participant=participant,
        defaults={"current_screen_key": get_first_screen_key()}
    )
    return progress
