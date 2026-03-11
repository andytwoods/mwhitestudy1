from django.db import models


class Question(models.Model):
    MULTIPLE_CHOICE = "multiple_choice"
    LIKERT = "likert"
    SLIDER = "slider"
    BINARY = "binary"
    NUMERIC = "numeric"
    FREE_TEXT = "free_text"
    QUESTION_TYPE_CHOICES = [
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (LIKERT, "Likert Scale"),
        (SLIDER, "Slider"),
        (BINARY, "Binary"),
        (NUMERIC, "Numeric"),
        (FREE_TEXT, "Free Text"),
    ]

    PRE_TRIAL = "pre_trial"
    INITIAL_JUDGEMENT = "initial_judgement"
    POST_FEEDBACK = "post_feedback"
    POST_TRIAL = "post_trial"
    END_OF_STUDY = "end_of_study"
    STAGE_CHOICES = [
        (PRE_TRIAL, "Pre-Trial"),
        (INITIAL_JUDGEMENT, "Initial Judgement"),
        (POST_FEEDBACK, "Post-Feedback"),
        (POST_TRIAL, "Post-Trial"),
        (END_OF_STUDY, "End of Study"),
    ]

    study = models.ForeignKey("study.Study", on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES)
    response_options = models.JSONField(null=True, blank=True)
    scale_min = models.FloatField(null=True, blank=True)
    scale_max = models.FloatField(null=True, blank=True)
    scale_step = models.FloatField(null=True, blank=True)
    condition_applicability = models.JSONField(default=list)
    stage_location = models.CharField(max_length=50, choices=STAGE_CHOICES)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["stage_location", "display_order"]

    def __str__(self):
        return f"[{self.stage_location}] {self.question_text[:60]}"


class FeedbackItem(models.Model):
    HUMAN = "human"
    AI = "ai"
    AGENT_TYPE_CHOICES = [
        (HUMAN, "Human"),
        (AI, "AI"),
    ]

    MALIGNANT = "malignant"
    BENIGN = "benign"
    DIAGNOSIS_CHOICES = [
        (MALIGNANT, "Malignant"),
        (BENIGN, "Benign"),
    ]

    image = models.ForeignKey("images.Image", on_delete=models.CASCADE, related_name="feedback_items")
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPE_CHOICES)
    diagnosis = models.CharField(max_length=50, choices=DIAGNOSIS_CHOICES)
    confidence = models.FloatField()
    source_label = models.CharField(max_length=100)
    imported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_label} ({self.agent_type}) → {self.diagnosis} [{self.image.external_id}]"


class Trial(models.Model):
    MALIGNANT = "malignant"
    BENIGN = "benign"
    GROUND_TRUTH_CHOICES = [
        (MALIGNANT, "Malignant"),
        (BENIGN, "Benign"),
    ]

    CORRECT = "correct"
    WRONG = "wrong"
    NA = "na"
    FEEDBACK_ACCURACY_CHOICES = [
        (CORRECT, "Correct"),
        (WRONG, "Wrong"),
        (NA, "N/A"),
    ]

    participant = models.ForeignKey(
        "participants.ParticipantSession",
        on_delete=models.CASCADE,
        related_name="trials",
    )
    condition = models.ForeignKey(
        "study.Condition",
        on_delete=models.PROTECT,
        related_name="trials",
    )
    image = models.ForeignKey("images.Image", on_delete=models.PROTECT, related_name="trials")
    image_ground_truth = models.CharField(max_length=50, choices=GROUND_TRUTH_CHOICES)
    block_position = models.PositiveSmallIntegerField(db_index=True)
    trial_position = models.PositiveSmallIntegerField(db_index=True)
    is_practice = models.BooleanField(default=False, db_index=True)
    is_catch_trial = models.BooleanField(default=False)
    feedback_presented = models.JSONField(null=True, blank=True)
    feedback_accuracy = models.CharField(max_length=50, choices=FEEDBACK_ACCURACY_CHOICES, default=NA)
    feedback_consensus_level = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_practice", "block_position", "trial_position"]

    def __str__(self):
        return f"Trial {self.trial_position} (block {self.block_position}) — {self.participant}"


class Response(models.Model):
    PRE_TRIAL = "pre_trial"
    INITIAL_JUDGEMENT = "initial_judgement"
    POST_FEEDBACK = "post_feedback"
    POST_TRIAL = "post_trial"
    END_OF_STUDY = "end_of_study"
    STAGE_CHOICES = [
        (PRE_TRIAL, "Pre-Trial"),
        (INITIAL_JUDGEMENT, "Initial Judgement"),
        (POST_FEEDBACK, "Post-Feedback"),
        (POST_TRIAL, "Post-Trial"),
        (END_OF_STUDY, "End of Study"),
    ]

    participant = models.ForeignKey(
        "participants.ParticipantSession",
        on_delete=models.CASCADE,
        related_name="responses",
    )
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="responses")
    response_value = models.CharField(max_length=100)
    response_timestamp = models.DateTimeField()
    stage_location = models.CharField(max_length=50, choices=STAGE_CHOICES, db_index=True)
    client_rt_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = [("trial", "question")]

    def __str__(self):
        return f"Response to {self.question} by {self.participant}"
