re# Study Design Recommendations

Critical evaluation of `online_study_specification.md`.

---

## 1. Blocked vs. Fully Randomised Trial Order — RESOLVED

Trials are blocked by condition. Block order is fully randomised per participant (no position constraints on any condition). Trial order within each block is also randomised. Block position is stored per participant and must be included as a covariate in analysis to control for learning/fatigue confounds.

---

## 2. Carryover / Contrast Effects — RESOLVED

Full randomisation of block order (no position constraints). Residual carryover controlled statistically via `block_position` as a fixed effect in the GLMM, and acknowledged as an inherent within-subjects limitation in the paper. Breaks between blocks implemented. Full analysis strategy now committed to in the spec (Analysis Strategy section).

---

## 3. Learning / Fatigue Effects — RESOLVED

- **Practice trials** added: a pre-study practice block using images outside the main bank, excluded from analysis, familiarises participants with both feedback and no-feedback interfaces.
- **Attention checks** added: 2–3 checks (IMC + catch trial + optional infrequency item), placed early and mid-study. Exclusion threshold: ≥2 failures (per Prolific policy for studies ≥5 min). RT flagging as supplementary indicator.
- **Breaks between blocks** added: mandatory rest screen between each condition block, participant-dismissed.
- **Block position and trial position** both recorded and included as fixed effects in the mixed model.
- Session duration estimate removed (not needed for implementation).

---

## 4. Image Assignment — RESOLVED

- Images drawn from a central bank; each image used at most once per participant.
- Malignant/benign cases equally distributed across all four conditions per participant.
- Across participants, images distributed approximately equally across conditions via random assignment with a balancing constraint.
- Image identity recorded per trial and included as a **random effect** in the mixed model to account for image difficulty variability.

---

## 5 & 6. Feedback Wrongness and Signal Detection Theory — RESOLVED

These two issues are interdependent and are addressed together.

### Wrongness definition

"Wrongness" is feedback that is **opposite to the correct answer** (e.g. the agent diagnoses malignant when ground truth is benign). It is a within-condition factor: some trials in each feedback condition present correct feedback, others present wrong feedback.

### Why 50/50 correct/wrong does not work

Equally distributing wrong and correct trials was considered but rejected for two reasons:

1. **SDT power:** A 50/50 split creates 8 cells (4 conditions × 2 feedback accuracy levels), each with ~5 trials and only ~2–3 signal or noise observations. Individual-level d' from 2–3 trials is essentially noise.
2. **Ecological validity:** A 50% error rate is unrealistic. Participants who notice that feedback is wrong half the time will stop trusting it, collapsing the social influence manipulation.

### Agreed approach

- Wrongness rate: **25%**, uniform across all agent types (`FEEDBACK_WRONG_RATE = 0.25`). Uniform rate keeps agent type and reliability orthogonal.
- Feedback accuracy (correct / wrong) included as a **factor in the GLMM**.
- SDT (d' and criterion) analysed at the **group level**, pooling trials across participants within each condition × feedback-accuracy cell. Individual-level SDT not attempted; acknowledged as underpowered in limitations.
- Consensus: **fixed at unanimity** (`FEEDBACK_CONSENSUS = "unanimous"`). Varying consensus deferred to a future study.
- Agents: 3 × "Consultant Radiologist" for human conditions, 1 × "AI Diagnostic System" for AI conditions. Human count identical across `human` and `human_ai` conditions.
- This approach is pre-registered.

---

## 7. Missing Measures — RESOLVED

- **Medical background**: single self-report item (none / informal / student / qualified professional), stored as `medical_training_level`, used as covariate.
- **Trust in AI (pre-measure)**: Jian et al. (2000) Checklist for Trust between People and Automation, 12-item 7-point Likert adapted for AI, administered before any feedback exposure, stored as `ai_trust_pre_score`.
- **Manipulation check**: post-study items verifying participants noticed and attended to feedback; participants failing despite being in a feedback condition flagged for sensitivity analysis.
- **Demand characteristics**: open-ended item administered last; responses coded 0–2 blind to condition; full-awareness participants (score 2) excluded from primary analysis, included in sensitivity analysis.
- **Payment**: £10/hour × 1.5 × estimated 48 min = **£12.00** (1.5× uplift for specialist medical pool), to be validated against pilot data.

---

## 8. Prolific Integration — RESOLVED

- **Completion redirect**: view redirects to `https://app.prolific.com/submissions/complete?cc=<PROLIFIC_COMPLETION_CODE>` on success; code stored in `settings.py`.
- **Partial completions**: data retained with `completion_status = "partial"`, excluded from primary analysis, retained for dropout analysis; not redirected to completion URL.
- **Prescreening**: age 18+, fluent English, **any medical/nursing/radiography training (student or qualified)**, normal/corrected vision, Prolific approval rate ≥ 90%. Restricting to trained participants ensures d' > 0 and ecological validity of the feedback manipulation.

---

## Status Summary

All design issues resolved. Remaining actions are post-piloting tasks:

- **Validate session duration and payment** against pilot data; adjust £12.00 if median duration differs materially from 48 min estimate
- **Pre-register** analysis strategy on OSF before data collection begins
