from django import forms

from mwhitestudy1.participants.models import PreStudyMeasure

_LIKERT_CHOICES = [(str(i), str(i)) for i in range(1, 8)]

# Jian et al. (2000) Checklist for Trust between People and Automation,
# adapted to refer to AI systems.
_AI_TRUST_ITEMS = [
    (1,  "The AI system is deceptive."),
    (2,  "The AI system behaves in an underhanded manner."),
    (3,  "I am suspicious of the AI system's intent, action, or outputs."),
    (4,  "I am wary of the AI system."),
    (5,  "The AI system's actions will have a harmful or injurious outcome."),
    (6,  "I am confident in the AI system."),
    (7,  "The AI system provides security."),
    (8,  "The AI system has integrity."),
    (9,  "The AI system is dependable."),
    (10, "The AI system is reliable."),
    (11, "I can trust the AI system."),
    (12, "I am familiar with the AI system."),
]


class MedicalBackgroundForm(forms.Form):
    medical_training_level = forms.ChoiceField(
        choices=PreStudyMeasure.TRAINING_CHOICES,
        widget=forms.RadioSelect,
        label="What best describes your medical training?",
    )


class AITrustForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for num, label in _AI_TRUST_ITEMS:
            self.fields[f"item_{num}"] = forms.ChoiceField(
                choices=_LIKERT_CHOICES,
                widget=forms.RadioSelect,
                label=label,
            )

    def item_fields(self):
        """Return (item_number, label, field) triples for template rendering."""
        for num, label in _AI_TRUST_ITEMS:
            yield num, label, self[f"item_{num}"]

    def compute_score(self) -> float:
        """Mean of all 12 item responses, rounded to 4 decimal places."""
        values = [int(self.cleaned_data[f"item_{num}"]) for num, _ in _AI_TRUST_ITEMS]
        return round(sum(values) / len(values), 4)

    def get_item_responses(self) -> dict:
        """Return responses keyed by item number string, as stored in JSON."""
        return {str(num): int(self.cleaned_data[f"item_{num}"]) for num, _ in _AI_TRUST_ITEMS}
