from django import forms


class ManipulationCheckForm(forms.Form):
    NOTICED_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
        ("unsure", "Unsure"),
    ]
    noticed_feedback = forms.ChoiceField(
        choices=NOTICED_CHOICES,
        widget=forms.RadioSelect,
        label="During the study, did you see assessments from other people or AI systems?",
    )
    attention_to_feedback = forms.IntegerField(
        min_value=1, max_value=7,
        widget=forms.NumberInput(attrs={"type": "range", "min": 1, "max": 7, "step": 1}),
        label="How much did you pay attention to the feedback you were shown? (1 = not at all, 7 = completely)",
    )
    influence_of_feedback = forms.IntegerField(
        min_value=1, max_value=7,
        widget=forms.NumberInput(attrs={"type": "range", "min": 1, "max": 7, "step": 1}),
        label="How much did the feedback influence your judgements? (1 = not at all, 7 = a great deal)",
    )


class DemandAwarenessForm(forms.Form):
    demand_awareness_response = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        label="In your own words, what do you think this study was investigating?",
        required=True,
    )
