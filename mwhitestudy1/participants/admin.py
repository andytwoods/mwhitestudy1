from django.contrib import admin

from .models import AttentionCheckResponse
from .models import ConsentRecord
from .models import DebriefRecord
from .models import ParticipantSession
from .models import PostStudyMeasure
from .models import PreStudyMeasure


class ConsentRecordInline(admin.StackedInline):
    model = ConsentRecord
    extra = 0
    readonly_fields = ["consent_timestamp"]


class DebriefRecordInline(admin.StackedInline):
    model = DebriefRecord
    extra = 0
    readonly_fields = ["debrief_timestamp"]


class AttentionCheckInline(admin.TabularInline):
    model = AttentionCheckResponse
    extra = 0
    readonly_fields = ["check_number", "check_type", "response_value", "passed"]


@admin.register(ParticipantSession)
class ParticipantSessionAdmin(admin.ModelAdmin):
    list_display = [
        "prolific_pid",
        "study",
        "completion_status",
        "attention_checks_failed",
        "excluded_inattentive",
        "median_trial_rt",
        "entry_timestamp",
    ]
    list_filter = ["study", "completion_status", "excluded_inattentive"]
    search_fields = ["prolific_pid", "prolific_study_id"]
    readonly_fields = ["entry_timestamp", "django_session_key"]
    inlines = [ConsentRecordInline, DebriefRecordInline, AttentionCheckInline]


@admin.register(PreStudyMeasure)
class PreStudyMeasureAdmin(admin.ModelAdmin):
    list_display = ["participant", "medical_training_level", "ai_trust_pre_score"]
    list_filter = ["medical_training_level"]


@admin.register(PostStudyMeasure)
class PostStudyMeasureAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "noticed_feedback",
        "attention_to_feedback",
        "influence_of_feedback",
        "demand_awareness_coded",
    ]
    list_filter = ["noticed_feedback", "demand_awareness_coded"]
