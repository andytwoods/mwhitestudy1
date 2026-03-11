import logging

from django.core.management.base import BaseCommand

from mwhitestudy1.study.helpers.config_loader import get_or_create_active_study
from mwhitestudy1.study.helpers.config_loader import load_active_study_config
from mwhitestudy1.study.models import Condition
from mwhitestudy1.study.models import FeedbackAgentDefinition
from mwhitestudy1.trials.models import Question

logger = logging.getLogger(__name__)

# Standard initial question set for this study design.
# Questions are identified by (stage_location, display_order) for idempotency.
_INITIAL_QUESTIONS = [
    {
        "stage_location": Question.INITIAL_JUDGEMENT,
        "display_order": 1,
        "question_text": "Based on the image, what is your diagnosis?",
        "question_type": Question.BINARY,
        "response_options": ["malignant", "benign"],
        "condition_applicability": [],
        "scale_min": None,
        "scale_max": None,
        "scale_step": None,
    },
    {
        "stage_location": Question.INITIAL_JUDGEMENT,
        "display_order": 2,
        "question_text": "How confident are you in your diagnosis? (0 = not at all, 100 = completely certain)",
        "question_type": Question.SLIDER,
        "response_options": None,
        "condition_applicability": [],
        "scale_min": 0.0,
        "scale_max": 100.0,
        "scale_step": 1.0,
    },
    {
        "stage_location": Question.POST_FEEDBACK,
        "display_order": 1,
        "question_text": "After seeing the feedback, what is your updated diagnosis?",
        "question_type": Question.BINARY,
        "response_options": ["malignant", "benign"],
        "condition_applicability": [Condition.HUMAN, Condition.HUMAN_AI, Condition.AI],
        "scale_min": None,
        "scale_max": None,
        "scale_step": None,
    },
    {
        "stage_location": Question.POST_FEEDBACK,
        "display_order": 2,
        "question_text": "After seeing the feedback, how confident are you in your diagnosis? (0 = not at all, 100 = completely certain)",
        "question_type": Question.SLIDER,
        "response_options": None,
        "condition_applicability": [Condition.HUMAN, Condition.HUMAN_AI, Condition.AI],
        "scale_min": 0.0,
        "scale_max": 100.0,
        "scale_step": 1.0,
    },
    {
        "stage_location": Question.POST_FEEDBACK,
        "display_order": 3,
        "question_text": "How much do you trust the feedback you just received? (1 = not at all, 7 = completely)",
        "question_type": Question.LIKERT,
        "response_options": None,
        "condition_applicability": [Condition.HUMAN, Condition.HUMAN_AI, Condition.AI],
        "scale_min": 1.0,
        "scale_max": 7.0,
        "scale_step": 1.0,
    },
    {
        "stage_location": Question.POST_FEEDBACK,
        "display_order": 4,
        "question_text": "How useful was the feedback in helping you make your diagnosis? (1 = not at all, 7 = extremely useful)",
        "question_type": Question.LIKERT,
        "response_options": None,
        "condition_applicability": [Condition.HUMAN, Condition.HUMAN_AI, Condition.AI],
        "scale_min": 1.0,
        "scale_max": 7.0,
        "scale_step": 1.0,
    },
]

_REQUIRED_CONFIG_KEYS = {"study_id", "trials_per_condition", "feedback_agents", "feedback_wrong_rate"}


class Command(BaseCommand):
    help = "Bootstrap the active study from its JSON config. Safe to re-run (idempotent)."

    def handle(self, *args, **options):
        config = load_active_study_config()

        missing = _REQUIRED_CONFIG_KEYS - config.keys()
        if missing:
            raise KeyError(f"Missing required key(s) in study config: {', '.join(sorted(missing))}")

        study = get_or_create_active_study()
        self.stdout.write(f"Study: {study}")

        # Conditions
        condition_names = list(config["trials_per_condition"].keys())
        for order, name in enumerate(condition_names):
            condition, created = Condition.objects.get_or_create(
                study=study,
                name=name,
                defaults={"display_order": order},
            )
            action = "Created" if created else "Exists"
            self.stdout.write(f"  {action} condition: {name}")

            # FeedbackAgentDefinitions for this condition
            for agent_def in config.get("feedback_agents", {}).get(name, []):
                _, created = FeedbackAgentDefinition.objects.get_or_create(
                    condition=condition,
                    agent_type=agent_def["type"],
                    label=agent_def["label"],
                    defaults={"count": agent_def["count"]},
                )
                if created:
                    self.stdout.write(f"    Created agent: {agent_def['label']} ({agent_def['type']})")

        # Questions
        for q_data in _INITIAL_QUESTIONS:
            _, created = Question.objects.get_or_create(
                study=study,
                stage_location=q_data["stage_location"],
                display_order=q_data["display_order"],
                defaults={
                    "question_text": q_data["question_text"],
                    "question_type": q_data["question_type"],
                    "response_options": q_data["response_options"],
                    "condition_applicability": q_data["condition_applicability"],
                    "scale_min": q_data["scale_min"],
                    "scale_max": q_data["scale_max"],
                    "scale_step": q_data["scale_step"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  Created question: [{q_data['stage_location']}] order={q_data['display_order']}")

        self.stdout.write(self.style.SUCCESS("Bootstrap complete."))
