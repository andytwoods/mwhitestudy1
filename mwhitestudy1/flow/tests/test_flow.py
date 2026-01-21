from django.test import TestCase, Client
from django.urls import reverse
from mwhitestudy1.flow.models import Participant, Progress, Response, ScreenEvent

class FlowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_start_study_creates_participant(self):
        url = reverse("flow:start", kwargs={"study_slug": "demo"})
        response = self.client.get(url)
        assert response.status_code == 200
        assert "participant_id" in self.client.session
        assert Participant.objects.count() == 1
        assert Progress.objects.count() == 1
        assert ScreenEvent.objects.filter(event_type="render").count() == 1

    def test_start_study_force_new_participant(self):
        url = reverse("flow:start", kwargs={"study_slug": "demo"})
        # First request to create a participant
        self.client.get(url)
        first_participant_id = self.client.session["participant_id"]
        assert Participant.objects.count() == 1

        # Second request with ?participant=new
        response = self.client.get(url + "?participant=new")
        assert response.status_code == 200
        second_participant_id = self.client.session["participant_id"]

        assert first_participant_id != second_participant_id
        assert Participant.objects.count() == 2
        assert Progress.objects.count() == 2

    def test_submit_valid_answer_advances_progress(self):
        # Initialize session
        self.client.get(reverse("flow:start", kwargs={"study_slug": "demo"}))

        url = reverse("flow:answer", kwargs={"study_slug": "demo", "screen_key": "start"})
        data = {"name": "Test User", "age": "25"}
        response = self.client.post(url, data)

        assert response.status_code == 200
        # Should render the next screen (interstitial_1)
        assert 'data-screen-key="interstitial_1"' in response.content.decode()

        participant = Participant.objects.first()
        assert Progress.objects.get(participant=participant).current_screen_key == "interstitial_1"
        assert Response.objects.filter(participant=participant, screen_key="start").count() == 2

    def test_submit_invalid_answer_shows_errors(self):
        self.client.get(reverse("flow:start", kwargs={"study_slug": "demo"}))

        url = reverse("flow:answer", kwargs={"study_slug": "demo", "screen_key": "start"})
        data = {"name": "", "age": "not-a-number"}
        response = self.client.post(url, data)

        assert response.status_code == 200
        assert "This field is required." in response.content.decode()
        assert "Please enter a valid number." in response.content.decode()

        participant = Participant.objects.first()
        assert Progress.objects.get(participant=participant).current_screen_key == "start"

    def test_continue_screen_fragment_load(self):
        self.client.get(reverse("flow:start", kwargs={"study_slug": "demo"}))

        url = reverse("flow:screen", kwargs={"study_slug": "demo", "screen_key": "interstitial_1"})
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'Press <strong>Space</strong> to continue' in response.content.decode()

        participant = Participant.objects.first()
        assert Progress.objects.get(participant=participant).current_screen_key == "interstitial_1"
