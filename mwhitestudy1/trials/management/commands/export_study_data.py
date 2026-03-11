import csv
import sys

from django.core.management.base import BaseCommand

from mwhitestudy1.trials.models import Response


class Command(BaseCommand):
    help = "Export all Response data to CSV for GLMM analysis."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="-",
            help="Output file path (default: stdout)",
        )
        parser.add_argument(
            "--study-slug",
            type=str,
            default=None,
            help="Filter to a specific study slug (default: all studies)",
        )

    def handle(self, *args, **options):
        qs = (
            Response.objects.select_related(
                "participant__study",
                "participant__pre_study_measure",
                "trial__condition",
                "trial__image",
                "question",
            )
            .order_by("participant_id", "trial__block_position", "trial__trial_position")
        )

        if options["study_slug"]:
            qs = qs.filter(participant__study__slug=options["study_slug"])

        fieldnames = [
            "participant_id",
            "prolific_pid",
            "study_slug",
            "condition",
            "block_position",
            "trial_position",
            "image_id",
            "image_ground_truth",
            "feedback_accuracy",
            "is_practice",
            "is_catch_trial",
            "question_id",
            "stage_location",
            "response_value",
            "response_timestamp",
            "client_rt_ms",
            "medical_training_level",
            "ai_trust_pre_score",
            "excluded_inattentive",
            "completion_status",
        ]

        output = sys.stdout if options["output"] == "-" else open(options["output"], "w", newline="", encoding="utf-8")
        try:
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for resp in qs.iterator(chunk_size=500):
                p = resp.participant
                trial = resp.trial
                pre = getattr(p, "pre_study_measure", None)
                writer.writerow({
                    "participant_id": p.pk,
                    "prolific_pid": p.prolific_pid,
                    "study_slug": p.study.slug,
                    "condition": trial.condition.name,
                    "block_position": trial.block_position,
                    "trial_position": trial.trial_position,
                    "image_id": trial.image.external_id,
                    "image_ground_truth": trial.image_ground_truth,
                    "feedback_accuracy": trial.feedback_accuracy,
                    "is_practice": trial.is_practice,
                    "is_catch_trial": trial.is_catch_trial,
                    "question_id": resp.question_id,
                    "stage_location": resp.stage_location,
                    "response_value": resp.response_value,
                    "response_timestamp": resp.response_timestamp.isoformat(),
                    "client_rt_ms": resp.client_rt_ms,
                    "medical_training_level": pre.medical_training_level if pre else "",
                    "ai_trust_pre_score": pre.ai_trust_pre_score if pre else "",
                    "excluded_inattentive": p.excluded_inattentive,
                    "completion_status": p.completion_status,
                })
        finally:
            if output is not sys.stdout:
                output.close()

        self.stdout.write(self.style.SUCCESS("Export complete."))
