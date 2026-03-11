from django.db import models


class Study(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    config_json = models.JSONField()
    is_active = models.BooleanField(default=False)
    consent_html = models.TextField()
    consent_version = models.CharField(max_length=20)
    debrief_html = models.TextField()
    debrief_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "studies"

    def __str__(self):
        return self.name


class Condition(models.Model):
    BASELINE = "baseline"
    HUMAN = "human"
    HUMAN_AI = "human_ai"
    AI = "ai"
    CONDITION_CHOICES = [
        (BASELINE, "Baseline"),
        (HUMAN, "Human"),
        (HUMAN_AI, "Human + AI"),
        (AI, "AI"),
    ]

    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="conditions")
    name = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]
        unique_together = [("study", "name")]

    def __str__(self):
        return f"{self.study} — {self.get_name_display()}"


class FeedbackAgentDefinition(models.Model):
    HUMAN = "human"
    AI = "ai"
    AGENT_TYPE_CHOICES = [
        (HUMAN, "Human"),
        (AI, "AI"),
    ]

    condition = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name="feedback_agents")
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPE_CHOICES)
    label = models.CharField(max_length=100)
    count = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.label} ({self.agent_type}) ×{self.count}"
