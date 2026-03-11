from django.shortcuts import redirect
from django.urls import reverse

from mwhitestudy1.participants.models import ParticipantSession


class ParticipantSessionMixin:
    """Retrieve the active ParticipantSession from the Django session.

    Sets ``self.participant`` on the view. Redirects to the entry URL if no
    valid session exists. Redirects to the completion URL if the participant
    has already finished.
    """

    def dispatch(self, request, *args, **kwargs):
        participant_id = request.session.get("participant_id")
        if not participant_id:
            return redirect(reverse("participants:entry"))
        try:
            self.participant = ParticipantSession.objects.get(pk=participant_id)
        except ParticipantSession.DoesNotExist:
            return redirect(reverse("participants:entry"))
        if self.participant.completion_status == ParticipantSession.COMPLETE:
            return redirect(reverse("participants:complete"))
        return super().dispatch(request, *args, **kwargs)
