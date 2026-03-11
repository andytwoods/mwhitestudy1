import factory
from factory.django import DjangoModelFactory

from mwhitestudy1.participants.models import AttentionCheckResponse
from mwhitestudy1.participants.models import ConsentRecord
from mwhitestudy1.participants.models import DebriefRecord
from mwhitestudy1.participants.models import ParticipantSession
from mwhitestudy1.participants.models import PostStudyMeasure
from mwhitestudy1.participants.models import PreStudyMeasure
from mwhitestudy1.study.tests.factories import StudyFactory


class ParticipantSessionFactory(DjangoModelFactory):
    class Meta:
        model = ParticipantSession

    study = factory.SubFactory(StudyFactory)
    prolific_pid = factory.Sequence(lambda n: f"PID{n:06d}")
    prolific_study_id = "STUDY001"
    prolific_session_id = factory.Sequence(lambda n: f"SESSION{n:06d}")
    ip_address = "127.0.0.1"
    django_session_key = factory.Sequence(lambda n: f"sessionkey{n:020d}")
    completion_status = ParticipantSession.IN_PROGRESS
    condition_order = ["baseline", "human", "human_ai", "ai"]
    study_version = factory.LazyAttribute(lambda o: o.study.config_json)


class ConsentRecordFactory(DjangoModelFactory):
    class Meta:
        model = ConsentRecord

    participant = factory.SubFactory(ParticipantSessionFactory)
    consent_html = "<p>Consent text.</p>"
    consent_version = "1.0"
    consent_given = True


class DebriefRecordFactory(DjangoModelFactory):
    class Meta:
        model = DebriefRecord

    participant = factory.SubFactory(ParticipantSessionFactory)
    debrief_html = "<p>Debrief text.</p>"
    debrief_version = "1.0"


class PreStudyMeasureFactory(DjangoModelFactory):
    class Meta:
        model = PreStudyMeasure

    participant = factory.SubFactory(ParticipantSessionFactory)
    medical_training_level = PreStudyMeasure.UNDERGRADUATE
    ai_trust_pre_score = 4.5
    ai_trust_items = {str(i): 4 for i in range(1, 13)}


class PostStudyMeasureFactory(DjangoModelFactory):
    class Meta:
        model = PostStudyMeasure

    participant = factory.SubFactory(ParticipantSessionFactory)
    noticed_feedback = PostStudyMeasure.YES
    attention_to_feedback = 5
    influence_of_feedback = 4
    demand_awareness_response = "I think it was about feedback."
    demand_awareness_coded = 0


class AttentionCheckResponseFactory(DjangoModelFactory):
    class Meta:
        model = AttentionCheckResponse

    participant = factory.SubFactory(ParticipantSessionFactory)
    check_number = 1
    check_type = AttentionCheckResponse.IMC
    response_value = "correct_answer"
    passed = True
