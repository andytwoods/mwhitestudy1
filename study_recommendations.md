re# Study Design Recommendations

Critical evaluation of `online_study_specification.md`.

---

## 1. Blocked vs. Fully Randomised Trial Order

The spec is ambiguous. It says "randomise condition order" and "randomise trial order within condition" — implying a blocked design, but never stating this explicitly.

**Blocked is almost certainly the right call** because:
- Each condition requires fundamentally different UI (feedback shown or not) — interleaving would be jarring
- Switching between "you get AI feedback" and "you get nothing" mid-session would make the manipulation transparent

**The spec should explicitly state:**
- Trials are **blocked by condition** (condition order randomised, trial order within each block randomised)
- Whether baseline is **position-constrained** (e.g., always first as a clean "no expectation" measure, or fully randomised like other blocks)
- That **block position** should be stored and included as a covariate in analysis

---

## 2. Carryover / Contrast Effects — Serious Gap

The biggest methodological concern in a within-subjects design. Once someone has seen AI feedback in block 2, their baseline block 3 is contaminated — they know feedback is coming, they've formed opinions about AI accuracy, etc.

The spec mentions none of:
- Washout periods between blocks
- Constraints on baseline position (it arguably should always come first)
- Analysis strategy for order effects (ANOVA with order as factor, or mixed models with block position as covariate)

**Recommendation:** Either fix baseline as block 1, or at minimum commit to analysing order as an independent variable and power the study accordingly.

---

## 3. Learning / Fatigue Effects — Unaddressed

Participants will improve at classifying medical images over ~20 trials regardless of condition. This improvement will be correlated with condition order. The spec has no:
- Practice trials / familiarisation phase before real data collection begins
- Attention checks or catch trials
- Breaks between blocks
- Estimate of session duration / fatigue risk

---

## 4. Image Assignment — Underspecified

The spec mentions "balanced-ness" in the open design decisions but the database schema just stores `image_assignment` without defining the assignment logic. A concrete counterbalancing scheme is needed before implementation:

- Does each image appear in only one condition per participant?
- Across participants, should each image appear equally often in each condition? (This implies a Latin square or similar — complex to implement correctly)
- Are malignant/benign images equally distributed across conditions per participant?

---

## 5. Feedback Accuracy / Manipulation — Critical Gap

The spec mentions introducing "wrongness" from AI or human feedback to observe confidence shifts, but never defines:
- What accuracy rate the simulated AI/human feedback has
- Whether accuracy is fixed or varies (and how)
- Whether feedback accuracy is an independent variable or just noise
- How "high consensus" vs "low consensus" is operationally defined

This is arguably the core experimental manipulation and it is almost entirely unspecified.

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
