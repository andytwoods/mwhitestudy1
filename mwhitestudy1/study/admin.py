from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import Condition
from .models import FeedbackAgentDefinition
from .models import Study


class ConditionInline(admin.TabularInline):
    model = Condition
    extra = 0


class FeedbackAgentInline(admin.TabularInline):
    model = FeedbackAgentDefinition
    extra = 0


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ConditionInline]
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 20, "cols": 80})},
    }


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ["study", "name", "display_order"]
    list_filter = ["study", "name"]
    inlines = [FeedbackAgentInline]


@admin.register(FeedbackAgentDefinition)
class FeedbackAgentDefinitionAdmin(admin.ModelAdmin):
    list_display = ["condition", "agent_type", "label", "count"]
    list_filter = ["agent_type", "condition__study"]
