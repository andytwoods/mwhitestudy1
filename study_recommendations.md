re# Study Design Recommendations

Critical evaluation of `online_study_specification.md`.

---

## 1. Blocked vs. Fully Randomised Trial Order — RESOLVED

Trials are blocked by condition. Block order is fully randomised per participant (no position constraints on any condition). Trial order within each block is also randomised. Block position is stored per participant and must be included as a covariate in analysis to control for learning/fatigue confounds.

---

## 2. Carryover / Contrast Effects — Serious Gap

The biggest methodological concern in a within-subjects design. Once someone has seen AI feedback in block 2, their baseline block 3 is contaminated — they know feedback is coming, they've formed opinions about AI accuracy, etc.

Fixing baseline as block 1 is not a solution — it trades carryover for a systematic order confound (position 1 effects become inseparable from the "no feedback" effect). Full randomisation of block order including baseline is correct.

Carryover is instead managed by:
- Including block position as a covariate in the mixed model (already captured via `block_position`)
- Acknowledging residual carryover as a limitation of the within-subjects design
- Optionally adding short breaks between blocks to reduce fatigue-driven contamination

The spec should explicitly commit to this analysis strategy. It should also note that any residual carryover (e.g. participants knowing feedback is coming once they've seen one feedback block) is an inherent limitation of the within-subjects design, not a fixable implementation issue.

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

## 5. Feedback Accuracy / Manipulation — OPEN, DEFERRED

"Wrongness" is now defined in the spec as feedback that is **opposite to the correct answer** (e.g. the agent diagnoses malignant when ground truth is benign).

How to treat wrongness trials in the analysis is unresolved. Open questions:
- Should incorrect-feedback trials be a separate factor in the model, or a level within a feedback-accuracy factor?
- How frequently should wrongness occur — evenly distributed, rare/surprising, or fixed per condition?
- How does wrongness interact with consensus level (e.g. unanimous wrong vs. split)?
- Should wrongness be pre-registered as a manipulation or treated as exploratory?

**This decision is deferred. Do not implement feedback-accuracy logic until resolved.**

Also still unresolved:
- Overall accuracy rate of feedback agents (when not "wrong")
- Operational definition of high vs. low consensus

---

## 6. Signal Detection Theory — Power Problem

The spec mentions using SDT to estimate d' and criterion shift. SDT requires many trials per condition to produce reliable estimates — typically 20–40+ per condition. With only ~5 trials per condition per participant (20 images / 4 conditions), individual-level d' estimates will have enormous variance and be essentially unreliable.

Options:
- Increase trials per condition (increases session length)
- Analyse at the group level only
- Use a Bayesian SDT approach that handles sparse data better
- Acknowledge this as a limitation explicitly

---

## 7. Missing Measures

| Missing element | Why it matters |
|---|---|
| Individual differences: prior medical knowledge | Major moderator — a nurse vs. a layperson will respond very differently to the manipulations |
| Trust in AI (pre-measure) | Likely the strongest individual-difference moderator |
| Manipulation checks | Did participants actually read/notice the feedback? |
| Demand characteristics check | Do participants guess the study hypothesis? |
| Session duration estimate | Important for Prolific payment fairness (£2 may be too low) |

---

## 8. Prolific Integration — Incomplete

The spec captures Prolific entry parameters but does not mention:
- The **completion redirect URL** (Prolific requires a specific URL participants are sent to on completion to confirm payment)
- Handling of **partial completions** (participant drops out mid-block — is their data usable?)
- **Prescreening criteria** (age, medical training excluded or required?)

---

## Priority Order

1. Explicitly define blocked trial structure and baseline position constraint
2. Define the feedback manipulation precisely — accuracy rate, consensus logic, how "wrongness" is introduced
3. Address carryover effects — either constrain baseline to first block or commit to order analysis
4. Resolve image assignment counterbalancing scheme before implementation
5. Add a familiarisation phase (practice trials, excluded from dataset)
6. Reconsider SDT viability given ~5 trials per condition
7. Add Prolific completion URL to implementation requirements
