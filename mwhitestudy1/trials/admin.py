from django.contrib import admin

from .models import FeedbackItem
from .models import Question
from .models import Response
from .models import Trial


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "question_text_short",
        "study",
        "question_type",
        "stage_location",
        "display_order",
        "is_active",
    ]
    list_filter = ["study", "stage_location", "question_type", "is_active"]
    search_fields = ["question_text"]
    ordering = ["study", "stage_location", "display_order"]

    @admin.display(description="Question")
    def question_text_short(self, obj):
        return obj.question_text[:80]


@admin.register(FeedbackItem)
class FeedbackItemAdmin(admin.ModelAdmin):
    list_display = ["image", "agent_type", "diagnosis", "confidence", "source_label", "imported_at"]
    list_filter = ["agent_type", "diagnosis", "image__ground_truth"]
    search_fields = ["image__external_id", "source_label"]
    readonly_fields = ["imported_at"]


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "condition",
        "image",
        "block_position",
        "trial_position",
        "feedback_accuracy",
        "is_practice",
        "is_catch_trial",
    ]
    list_filter = [
        "condition__study",
        "condition__name",
        "feedback_accuracy",
        "is_practice",
        "is_catch_trial",
    ]
    search_fields = ["participant__prolific_pid"]
    raw_id_fields = ["participant", "image"]
    readonly_fields = ["created_at"]


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "trial",
        "question",
        "response_value",
        "stage_location",
        "response_timestamp",
    ]
    list_filter = ["stage_location", "question__study"]
    search_fields = ["participant__prolific_pid"]
    raw_id_fields = ["participant", "trial", "question"]
