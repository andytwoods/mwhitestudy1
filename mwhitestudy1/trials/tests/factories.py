import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from mwhitestudy1.images.tests.factories import ImageFactory
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory
from mwhitestudy1.study.tests.factories import ConditionFactory
from mwhitestudy1.study.tests.factories import StudyFactory
from mwhitestudy1.trials.models import FeedbackItem
from mwhitestudy1.trials.models import Question
from mwhitestudy1.trials.models import Response
from mwhitestudy1.trials.models import Trial


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    study = factory.SubFactory(StudyFactory)
    question_text = factory.Sequence(lambda n: f"Question {n}?")
    question_type = Question.BINARY
    response_options = [Question.BINARY, "malignant", "benign"]
    condition_applicability = []
    stage_location = Question.INITIAL_JUDGEMENT
    display_order = factory.Sequence(lambda n: n)
    is_active = True


class FeedbackItemFactory(DjangoModelFactory):
    class Meta:
        model = FeedbackItem

    image = factory.SubFactory(ImageFactory)
    agent_type = FeedbackItem.HUMAN
    diagnosis = FeedbackItem.MALIGNANT
    confidence = 0.85
    source_label = "Consultant Radiologist"


class TrialFactory(DjangoModelFactory):
    class Meta:
        model = Trial

    participant = factory.SubFactory(ParticipantSessionFactory)
    condition = factory.SubFactory(ConditionFactory)
    image = factory.SubFactory(ImageFactory)
    image_ground_truth = Trial.MALIGNANT
    block_position = 1
    trial_position = 1
    is_practice = False
    is_catch_trial = False
    feedback_presented = None
    feedback_accuracy = Trial.NA


class ResponseFactory(DjangoModelFactory):
    class Meta:
        model = Response

    participant = factory.SubFactory(ParticipantSessionFactory)
    trial = factory.SubFactory(TrialFactory)
    question = factory.SubFactory(QuestionFactory)
    response_value = "malignant"
    response_timestamp = factory.LazyFunction(timezone.now)
    stage_location = Response.INITIAL_JUDGEMENT
