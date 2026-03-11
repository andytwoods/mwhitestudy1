from django.db import models


class ParticipantSession(models.Model):
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    PARTIAL = "partial"
    STATUS_CHOICES = [
        (IN_PROGRESS, "In Progress"),
        (COMPLETE, "Complete"),
        (PARTIAL, "Partial"),
    ]

    study = models.ForeignKey(
        "study.Study",
        on_delete=models.PROTECT,
        related_name="participant_sessions",
    )
    prolific_pid = models.CharField(max_length=50, db_index=True)
    prolific_study_id = models.CharField(max_length=50)
    prolific_session_id = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    django_session_key = models.CharField(max_length=50, db_index=True)
    entry_timestamp = models.DateTimeField(auto_now_add=True)
    completion_timestamp = models.DateTimeField(null=True, blank=True)
    completion_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=IN_PROGRESS,
        db_index=True,
    )
    condition_order = models.JSONField(null=True, blank=True)
    study_version = models.JSONField(null=True, blank=True)
    excluded_inattentive = models.BooleanField(default=False)
    attention_checks_failed = models.IntegerField(default=0)
    median_trial_rt = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.prolific_pid} ({self.completion_status})"


class ConsentRecord(models.Model):
    participant = models.OneToOneField(
        ParticipantSession,
        on_delete=models.CASCADE,
        related_name="consent_record",
    )
    consent_html = models.TextField()
    consent_version = models.CharField(max_length=20)
    consent_given = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consent for {self.participant} — {'given' if self.consent_given else 'refused'}"


class DebriefRecord(models.Model):
    participant = models.OneToOneField(
        ParticipantSession,
        on_delete=models.CASCADE,
        related_name="debrief_record",
    )
    debrief_html = models.TextField()
    debrief_version = models.CharField(max_length=20)
    debrief_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Debrief for {self.participant}"


class PreStudyMeasure(models.Model):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"
    QUALIFIED_NURSE = "qualified_nurse"
    QUALIFIED_DOCTOR = "qualified_doctor"
    RADIOLOGIST = "radiologist"
    TRAINING_CHOICES = [
        (UNDERGRADUATE, "Undergraduate medical / nursing / radiography student"),
        (POSTGRADUATE, "Postgraduate / junior doctor / resident"),
        (QUALIFIED_NURSE, "Qualified nurse or allied health professional"),
        (QUALIFIED_DOCTOR, "Qualified doctor (non-specialist)"),
        (RADIOLOGIST, "Radiologist or specialist with imaging experience"),
    ]

    participant = models.OneToOneField(
        ParticipantSession,
        on_delete=models.CASCADE,
        related_name="pre_study_measure",
    )
    medical_training_level = models.CharField(max_length=50, choices=TRAINING_CHOICES)
    ai_trust_pre_score = models.FloatField(null=True, blank=True)
    ai_trust_items = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Pre-study measures for {self.participant}"


class PostStudyMeasure(models.Model):
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"
    NOTICED_CHOICES = [
        (YES, "Yes"),
        (NO, "No"),
        (UNSURE, "Unsure"),
    ]

    participant = models.OneToOneField(
        ParticipantSession,
        on_delete=models.CASCADE,
        related_name="post_study_measure",
    )
    noticed_feedback = models.CharField(max_length=50, choices=NOTICED_CHOICES)
    attention_to_feedback = models.IntegerField(null=True, blank=True)
    influence_of_feedback = models.IntegerField(null=True, blank=True)
    demand_awareness_response = models.TextField(blank=True)
    demand_awareness_coded = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Post-study measures for {self.participant}"


class AttentionCheckResponse(models.Model):
    IMC = "imc"
    CATCH_TRIAL = "catch_trial"
    INFREQUENCY = "infrequency"
    CHECK_TYPE_CHOICES = [
        (IMC, "Instructional Manipulation Check"),
        (CATCH_TRIAL, "Catch Trial"),
        (INFREQUENCY, "Infrequency Item"),
    ]

    participant = models.ForeignKey(
        ParticipantSession,
        on_delete=models.CASCADE,
        related_name="attention_check_responses",
    )
    check_number = models.PositiveSmallIntegerField()
    check_type = models.CharField(max_length=50, choices=CHECK_TYPE_CHOICES)
    response_value = models.CharField(max_length=100)
    passed = models.BooleanField(default=False)

    def __str__(self):
        status = "pass" if self.passed else "fail"
        return f"Check {self.check_number} for {self.participant} — {status}"
