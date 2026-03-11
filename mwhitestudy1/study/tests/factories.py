import factory
from factory.django import DjangoModelFactory

from mwhitestudy1.study.models import Condition
from mwhitestudy1.study.models import FeedbackAgentDefinition
from mwhitestudy1.study.models import Study


class StudyFactory(DjangoModelFactory):
    class Meta:
        model = Study

    name = factory.Sequence(lambda n: f"Study {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
    config_json = factory.LazyFunction(
        lambda: {
            "study_id": "study1",
            "payment_gbp": 12.00,
            "practice_trial_count": 5,
            "prolific_completion_code": "TESTCODE",
            "trials_per_condition": {"baseline": 5, "human": 5, "human_ai": 5, "ai": 5},
            "feedback_wrong_rate": 0.25,
            "feedback_consensus": "unanimous",
        }
    )
    is_active = True
    consent_html = "<p>Consent text.</p>"
    consent_version = "1.0"
    debrief_html = "<p>Debrief text.</p>"
    debrief_version = "1.0"


class ConditionFactory(DjangoModelFactory):
    class Meta:
        model = Condition

    study = factory.SubFactory(StudyFactory)
    name = factory.Iterator([Condition.BASELINE, Condition.HUMAN, Condition.HUMAN_AI, Condition.AI])
    display_order = factory.Sequence(lambda n: n)


class FeedbackAgentDefinitionFactory(DjangoModelFactory):
    class Meta:
        model = FeedbackAgentDefinition

    condition = factory.SubFactory(ConditionFactory)
    agent_type = FeedbackAgentDefinition.HUMAN
    label = "Consultant Radiologist"
    count = 3
