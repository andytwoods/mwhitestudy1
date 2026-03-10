# Online Study Specification -- Medical Image Judgement and Social/AI Feedback

## Overview

This document describes the current design specification for an online
behavioural experiment investigating how human and AI feedback
influences confidence and diagnostic judgements of medical images.

Participants will evaluate medical images and indicate whether they
believe the image depicts **malignant cancer** or **benign tissue**,
along with their **confidence** in this judgement. After their initial
judgement, they may be shown feedback from other agents depending on
condition, after which additional responses may be collected.

Participants will be recruited via **Prolific Academic**.

------------------------------------------------------------------------

# Ethical Documentation

## Ethics Approval

The study will be approved by the relevant university ethics committee
before deployment.

Participants will interact with two ethics-related documents.

## Participant Information / Consent Form

-   displayed at the beginning of the study
-   approved by the university ethics board
-   stored in the database as **HTML content**
-   the exact HTML version presented to participants must be stored

### Data stored

-   consent_html
-   consent_version
-   consent_timestamp
-   consent_given (boolean)

## Debrief Sheet

-   displayed at the end of the study
-   approved by the university ethics board
-   stored in the database as **HTML content**

### Data stored

-   debrief_html
-   debrief_version
-   debrief_timestamp

------------------------------------------------------------------------

# Recruitment

Participants will be recruited using **Prolific Academic**.

Participants will access the study via a URL containing Prolific
parameters.

Example:

https://study.example.com/start?PROLIFIC_PID=XXX&STUDY_ID=YYY&SESSION_ID=ZZZ

## Parameters captured

-   prolific_pid
-   prolific_study_id
-   prolific_session_id

## Additional stored data

-   entry_timestamp
-   completion_timestamp
-   completion_status

These parameters allow confirmation of completion and payment on
Prolific.

## Payment

Payment is set at **£10/hour** pro-rated to estimated study duration.

Estimated study duration: **~48 minutes** (see breakdown below).

| Phase | Estimated time |
|---|---|
| Consent + participant information sheet | 3 min |
| Pre-study questionnaires | 5 min |
| Practice block | 5 min |
| Baseline block (5 trials × ~50 s) | 4 min |
| 3 feedback blocks (15 trials × ~90 s) | 23 min |
| Inter-block breaks (3 × ~1 min) | 3 min |
| Post-study measures | 3 min |
| Debrief | 2 min |
| **Total** | **~48 min** |

Payment rate: £10 × 1.5 × (48/60) = **£12.00 per participant** (1.5× uplift for specialist medical participant pool).

This estimate should be validated against pilot data and the rate
adjusted before full deployment. The formula `£10/hour × actual_median_duration`
must be applied after piloting.

## Completion Redirect

On successful completion, participants are redirected to the Prolific
completion URL:

```
https://app.prolific.com/submissions/complete?cc=<COMPLETION_CODE>
```

The completion code is stored in `settings.py` as `PROLIFIC_COMPLETION_CODE`
and appended to the redirect URL by the study's completion view. This
confirms payment eligibility to Prolific.

## Partial Completions

If a participant abandons the study mid-session:

-   Their data up to the point of dropout is retained in the database
    with `completion_status = "partial"`.
-   They are **not** redirected to the Prolific completion URL.
-   Partial data is excluded from the primary analysis but retained for
    dropout analysis (e.g. do dropout rates differ by condition order?).
-   On Prolific, partial completions are returned/timed-out and not paid.

## Prescreening Criteria

-   Age 18+
-   Fluent English
-   **Medical training: any medical, nursing, or radiography training
    (student or qualified)** — screened via Prolific's custom screener
    or pre-study eligibility question
-   Normal or corrected-to-normal vision
-   Standard Prolific approval rate ≥ 90%

Note: restricting to participants with medical training ensures
baseline diagnostic sensitivity (d' > 0) and ecological validity of
the social influence manipulation. Participants with no medical
background cannot meaningfully weigh AI or peer feedback against their
own clinical judgement.

------------------------------------------------------------------------

# Pre-Study Measures

Collected after consent and before the practice block. These are
individual-difference measures used as covariates in analysis.

## Medical Background

A single self-report item capturing level of training (used as a
covariate to account for variation in baseline diagnostic accuracy):

> "What best describes your medical training?"

Response options:

-   Undergraduate medical / nursing / radiography student
-   Postgraduate / junior doctor / resident
-   Qualified nurse or allied health professional
-   Qualified doctor (non-specialist)
-   Radiologist or specialist with imaging experience

Stored as `medical_training_level`.

## Trust in AI (Pre-Measure)

Administered before any AI feedback is encountered, to capture
dispositional trust rather than experience-driven trust.

Use the **Jian et al. (2000) Checklist for Trust between People and
Automation** (12 items, 7-point Likert), adapted to refer to AI
systems. This is the most widely validated instrument for this
construct and has been used extensively in human-AI interaction
research.

Stored as `ai_trust_pre_score` (mean of 12 items).

------------------------------------------------------------------------

# Experimental Design

## Design Type

**Within-subjects design**

All participants experience all experimental conditions.

## Conditions

The study includes **four conditions**:

1.  baseline\
2.  human\
3.  human + AI\
4.  AI

Each participant will complete trials under **all four conditions**.

### Condition Definitions

#### Baseline condition

Participants view the medical image and make their own judgement.

They do **not** see any assessments from:

-   other humans
-   AI systems

This condition serves as a no-feedback comparison condition.

#### Human condition

Participants receive feedback from **human raters only**.

#### Human + AI condition

Participants receive feedback from:

-   humans
-   AI systems

#### AI condition

Participants receive feedback from **AI systems only**.

------------------------------------------------------------------------

# Trial Counts and Configuration

The study must support configurable numbers of trials per condition.

Rather than hard-coding the total number of trials, the Django
application should allow the researcher to specify the number of trials
for each condition via configuration, likely in `settings.py`.

Example configuration:

``` python
STUDY_TRIALS_PER_CONDITION = {
    "baseline": 10,
    "human": 10,
    "human_ai": 10,
    "ai": 10,
}
```

Total trials:

``` python
TOTAL_TRIALS = sum(STUDY_TRIALS_PER_CONDITION.values())
```

------------------------------------------------------------------------

# Trial Order Randomisation

## Structure

Trials are **blocked by condition**: all trials for a given condition run
together before the next condition begins. This avoids jarring mid-session
UI switches (e.g. between "feedback shown" and "no feedback") and prevents
the feedback manipulation from becoming immediately transparent to
participants.

## Randomisation

-   **Block order** is fully randomised per participant (no position
    constraints on any condition, including baseline).
-   **Trial order within each block** is randomised per participant.

## Breaks Between Blocks

A mandatory rest break is presented between each condition block. The
participant must actively dismiss the break screen before the next block
begins. This reduces fatigue-driven carryover and gives participants a
moment to reset before a new feedback condition.

## Order Effects

Block order (position 1–4) and trial order within each block (position
1–n) are both recorded per participant and included as factors in the
analysis (fixed effects in a mixed model). This controls for learning,
fatigue, and practice effects that may be confounded with condition
assignment.

## Stored per participant

-   condition_order (the randomised sequence of condition blocks)
-   trial_order (the randomised trial sequence within each block)
-   block_position (numeric position 1–4 for each condition)
-   trial_position (numeric position of each trial within its block)

------------------------------------------------------------------------

# Image Bank and Assignment

## Image Bank

All images are drawn from a central image bank stored in the database.
Each image has a known ground truth (malignant or benign).

## Assignment Per Participant

-   Images are randomly sampled from the bank for each participant.
-   Each image is used **at most once** per participant (no repeats).
-   Images are assigned to conditions such that malignant and benign
    cases are **equally distributed across all four conditions** per
    participant (e.g. if 5 trials per condition, each condition receives
    the same number of malignant and benign images).

## Assignment Across Participants

-   Across participants, images should be distributed approximately
    equally across conditions to avoid any single image being
    over-represented in one condition.
-   This is achieved by random assignment with a balancing constraint
    (not a strict Latin square), tracked in the database.

## Image as an Analysis Factor

Image identity is recorded for every trial and included as a random
effect in the mixed model to account for variability in image
difficulty.

## Stored per trial

-   image_id
-   image_ground_truth (malignant / benign)
-   condition the image was shown under for this participant

------------------------------------------------------------------------

# Practice Trials

Before the main study begins, participants complete a **practice block**
of trials using images that are **not** drawn from the main image bank
and are **excluded from all analysis**.

Purpose:

-   familiarise participants with the interface and response format
-   reduce early learning effects that would otherwise be confounded
    with whichever condition block comes first

The practice block should include at least one example of each response
type (diagnosis, confidence rating) and, where feasible, one example
with and one without feedback, so participants understand both
interfaces before real data collection begins.

Practice trial count and images are configured separately from
`STUDY_TRIALS_PER_CONDITION`.

------------------------------------------------------------------------

# Attention Checks

## Rationale

Prolific participants may respond carelessly, particularly in repetitive
perceptual tasks. Attention checks identify inattentive participants
for exclusion prior to analysis.

## Method

Two to three attention checks are embedded across the study, mixing
two check types:

### 1. Instructional Manipulation Check (IMC)

A real-looking question whose body text contains an embedded instruction
that overrides the apparent question (e.g. "People differ in their
views on medicine. To show you are reading carefully, please select
'Strongly disagree' regardless of your actual opinion."). Participants
must read the full item to comply.

### 2. Catch Trial

One trial in the main task uses an unambiguous image (very clearly
benign or very clearly malignant) for which the objectively correct
diagnosis is obvious. An incorrect response flags potential
inattention in the context of the actual task.

### 3. Infrequency / Bogus Item (optional third check)

A Likert-format statement that virtually no attentive person would
endorse (e.g. "I have never had any thoughts of any kind"). Endorsing
it signals careless responding.

## Placement

-   Check 1 (IMC): early in the study, within the first block.
-   Check 2 (catch trial): embedded naturally within a mid-study block.
-   Check 3 (infrequency item, if used): end of study questionnaire.

## Exclusion Criterion

Participants who fail **two or more** attention checks are excluded from
analysis. This is consistent with Prolific's policy for studies ≥5
minutes (Ward & Meade, 2023; Prolific researcher guidelines).

A single failure is flagged but does not trigger exclusion on its own.

## Supplementary Indicator

Response time is recorded for every trial. Implausibly fast responses
across all trials (e.g. below 10% of the sample median RT) are
flagged as a secondary careless-responding indicator and reported
alongside attention check failure rates.

## Stored per participant

-   attention_check_1_response
-   attention_check_2_response (catch trial)
-   attention_check_3_response (if used)
-   attention_checks_failed (count)
-   excluded_inattentive (boolean)
-   median_trial_rt

------------------------------------------------------------------------

# Task Structure

Each trial consists of a **medical image classification task**.

Participants view a medical image and provide:

-   diagnosis
-   confidence rating

Images depict either:

-   malignant cancer
-   benign tissue

------------------------------------------------------------------------

# Trial Flow

## Stage 1 -- Image Presentation

Participant is shown a medical image.

### Diagnosis

Question example:

Is the image malignant cancer or benign?

Responses:

-   malignant
-   benign

### Confidence

Question example:

How confident are you in your diagnosis?

Possible formats:

-   slider
-   Likert scale
-   probability estimate

------------------------------------------------------------------------

## Stage 2 -- Feedback Presentation

The same image remains visible.

Feedback depends on condition.

### Baseline

No feedback shown.

### Human

Human assessments displayed.

Example:

-   human diagnosis
-   human confidence

### Human + AI

Feedback from:

-   humans
-   AI systems

### AI

Feedback from AI systems only.

------------------------------------------------------------------------

## Stage 3 -- Additional Feedback Rounds (Optional)

The system may support multiple feedback rounds including:

-   sequential human responses
-   sequential AI responses
-   mixed sources

Baseline typically skips this stage.

------------------------------------------------------------------------

## Stage 4 -- Post-Feedback Questions

Participants may answer additional questions such as:

-   updated diagnosis
-   updated confidence
-   trust in feedback
-   perceived usefulness

------------------------------------------------------------------------

# Post-Study Measures

Collected after the final trial block, before the debrief screen.

## Manipulation Check

Verifies that participants noticed and processed the feedback shown
during the study.

Example items:

-   "During the study, did you see assessments from other people or AI
    systems?" (yes / no / unsure)
-   "How much did you pay attention to the feedback you were shown?"
    (7-point Likert: not at all → completely)
-   "How much did the feedback influence your judgements?" (7-point
    Likert: not at all → a great deal)

Participants who report not noticing any feedback despite being in a
feedback condition are flagged for sensitivity analysis.

## Demand Characteristics Check

Assesses whether participants guessed the study hypothesis, which would
threaten internal validity.

Open-ended item presented last (after all other post-study questions,
to avoid priming):

> "In your own words, what do you think this study was investigating?"

Responses are coded post-hoc (blind to condition) as:
- 0 = no awareness of hypothesis
- 1 = partial awareness
- 2 = full awareness (correctly identifies social influence / AI
  feedback as the focus)

Participants with full awareness (score 2) are excluded from the
primary analysis and included in a sensitivity analysis.

------------------------------------------------------------------------

# Database-Driven Question System

Questions must be **defined in the database**, not hard-coded.

Benefits:

-   easy study modification
-   condition-specific questions
-   stage-specific questions

## Question Fields

Each question should include:

-   question_id
-   question_text
-   question_type
-   response_options
-   scale_definition
-   condition_applicability
-   stage_location
-   display_order
-   active_flag

## Question Types

Supported types:

-   multiple choice
-   Likert scale
-   slider
-   binary
-   numeric
-   free text

## Question Placement

Example stage locations:

-   pre_trial
-   initial_judgement
-   post_feedback
-   post_trial
-   end_of_study

## Question Ordering

Questions shown according to `display_order` within each stage.

Example:

  stage_location      display_order   question
  ------------------- --------------- --------------------
  initial_judgement   1               diagnosis
  initial_judgement   2               confidence
  post_feedback       1               updated diagnosis
  post_feedback       2               updated confidence

------------------------------------------------------------------------

# Data Storage Requirements

## Participant-Level Data

Stored per participant:

-   prolific_pid
-   prolific_study_id
-   prolific_session_id
-   entry_timestamp
-   completion_timestamp
-   completion_status
-   study_version

## Study Configuration Snapshot

For reproducibility the system should store:

-   trials per condition
-   randomisation settings
-   active question set
-   consent version
-   debrief version

## Trial-Level Data

Stored per trial:

-   participant_id
-   trial_number
-   condition
-   condition_position
-   image_id
-   image_ground_truth
-   feedback_presented
-   timestamps

## Response-Level Data

Each response includes:

-   participant_id
-   trial_id
-   question_id
-   response_value
-   response_timestamp

------------------------------------------------------------------------

# Analysis Strategy

## Primary Model

Responses are analysed using a **generalised linear mixed model (GLMM)**
with the following structure:

**Fixed effects:**

-   `condition` (baseline / human / human+AI / AI) — primary IV
-   `feedback_accuracy` (correct / wrong) — within-condition factor;
    baseline trials excluded from this factor
-   `block_position` (1–4) — controls for order/fatigue/learning effects
    confounded with condition assignment
-   `trial_position` (position within block) — controls for within-block
    learning and fatigue
-   `medical_training_level` — individual-difference covariate
-   `ai_trust_pre_score` — individual-difference covariate

**Random effects:**

-   Random intercept per participant — accounts for individual baseline
    differences in diagnostic accuracy and confidence
-   Random intercept per image — accounts for variability in image
    difficulty

## Signal Detection Theory

d' (sensitivity) and criterion c are estimated at the **group level**
by pooling trials across participants within each
`condition × feedback_accuracy` cell. Individual-level SDT is not
attempted due to insufficient trials per cell (~5) and is acknowledged
as a limitation.

## Carryover Effects

Block order is fully randomised; no condition is position-constrained.
Residual carryover (e.g. participants anticipating feedback in later
blocks after experiencing it in earlier ones) is an inherent limitation
of the within-subjects design. It is controlled statistically via
`block_position` as a fixed effect and reported as a limitation in
the paper.

## Exclusions

The following participants are excluded from the **primary analysis**:

-   Failed ≥ 2 attention checks (`excluded_inattentive = True`)
-   Full awareness of study hypothesis on demand characteristics check
    (coded 2)
-   `completion_status = "partial"`

All excluded participants are retained for **sensitivity analyses**
reported alongside primary results.

## Pre-registration

The analysis strategy above is to be pre-registered (e.g. on OSF)
before data collection begins.

------------------------------------------------------------------------

# Implementation Notes

The study will be implemented as a **Django web application** designed
for reuse across multiple future studies with minimal code changes.

## Reusability Principles

The infrastructure must treat this study as one instance of a general
online experiment platform. Future studies may differ in:

-   image domain (not just cancer images)
-   number and type of conditions
-   feedback agent types, counts, and accuracy rates
-   question sets and response formats
-   trial counts per condition
-   consensus and wrongness rates

All study-specific parameters must be **configurable**, not hardcoded.

## Study Configuration Files

Each study is defined by a JSON config file (e.g. `study1.json`) stored
in a `study_configs/` directory. The platform loads the active study's
config at runtime via `ACTIVE_STUDY_CONFIG` in `settings.py`.

All study-specific parameters live in the JSON file, keeping `settings.py`
free of per-study values:

```json
{
    "study_id": "study1",
    "payment_gbp": 12.00,
    "practice_trial_count": 5,
    "prolific_completion_code": "...",
    "trials_per_condition": {
        "baseline": 5,
        "human": 5,
        "human_ai": 5,
        "ai": 5
    },
    "feedback_wrong_rate": 0.25,
    "feedback_consensus": "unanimous",
    "feedback_agents": {
        "human": [
            {"type": "human", "label": "Consultant Radiologist", "count": 3}
        ],
        "human_ai": [
            {"type": "human", "label": "Consultant Radiologist", "count": 3},
            {"type": "ai",    "label": "AI Diagnostic System",   "count": 1}
        ],
        "ai": [
            {"type": "ai",    "label": "AI Diagnostic System",   "count": 1}
        ]
    }
}
```

`settings.py` contains only the pointer to the active config:

```python
ACTIVE_STUDY_CONFIG = "study_configs/study1.json"
```

The full contents of the config file are stored in the per-session
configuration snapshot for reproducibility.

## Database-Driven Behaviour

The following must be defined in the database, not in code:

-   Questions, response types, and display order (already specified)
-   Conditions and their properties
-   Consent and debrief HTML (versioned)
-   Image bank (generic — not tied to any specific domain)
-   Feedback agent definitions (type, label, display properties)

## Multi-Study Support

The platform should support multiple studies coexisting in the same
Django instance. Each study has its own:

-   configuration snapshot (stored at the start of each participant
    session for reproducibility)
-   participant pool and data
-   consent/debrief versions

A `Study` model should act as the top-level object to which all
participants, trials, and responses belong, allowing the same codebase
to run future experiments without forking.

## Core Requirements

-   Capture Prolific parameters on entry
-   Store consent and debrief HTML (versioned)
-   Support configurable within-subject conditions
-   Configure trial counts, wrongness rate, and consensus via settings
-   Randomise block and trial order; record positions as analysis factors
-   Load questions dynamically from database
-   Record all responses with timestamps
-   Store full configuration snapshot per participant session
-   Redirect to Prolific completion URL on success

------------------------------------------------------------------------

## Considerations & Open Design Decisions

### 1. Sample Size and Data Density
Current projections from research notes suggest a target of **100 participants** recruited via Prolific.
* **Trial Density**: Each participant is expected to rate approximately **20 images**.
* **Total Data Points**: With 100 participants and 20 ratings each, the goal is to generate **2,000 unique assessment points**.
* **Budgeting**: Estimated payment is **£2 per participant**.
* **Complexity**: We cannot rely on simple randomization alone; the system must ensure "balanced-ness" so that images receive roughly equal exposure across the 4 conditions.

### 2. Temporal Realism and "The Gap"
A key psychological consideration is how the "feedback" is perceived by the participant.
* **The "Time Gap" Dilemma**: We must decide whether to **fake a time gap** to simulate a "live" diagnosis from a first human, or explicitly inform participants that they are viewing **historical data** from real humans.
* **Current Preference**: The notes lean toward telling humans the data was provided in the past but from real humans.

### 3. Social Dynamics: Human Experts and Consensus

#### Consensus

Consensus is **fixed at unanimity**: all agents shown on a given trial
agree on the same diagnosis. Varying consensus as an independent
variable is not feasible at current trial counts (~5 per condition) and
is deferred to a future study.

Consensus level is stored per trial (`feedback_consensus_level`) and
configured via `settings.py` as `FEEDBACK_CONSENSUS = "unanimous"` to
allow future studies to vary this without code changes.

#### Wrongness

"Wrongness" is defined as feedback **opposite to the correct answer**
(e.g. all agents diagnose malignant when ground truth is benign).

-   Wrongness rate: **25%** of feedback trials, uniform across all
    agent types (human and AI). Using different rates per agent type
    would confound agent type with reliability, making it impossible to
    attribute condition differences cleanly to agent type.
-   Configured in `settings.py` as `FEEDBACK_WRONG_RATE = 0.25`.
-   Feedback accuracy (correct / wrong) is a factor in the GLMM.
-   SDT is analysed at group level only (individual-level is
    underpowered at ~5 trials per condition).

#### Agent Quantity and Status

The number of agents shown per condition and their displayed expertise
label are defined in the study's JSON config file (see Study
Configuration Files below). This is study-specific — different studies
use different config files with no code or `settings.py` changes
required.

`label` controls the expertise framing shown to participants. `count`
controls how many independent assessments from that agent type are
displayed. `baseline` is omitted as no agents are shown.

The agreed configuration is:

- **Human agents:** 3 × "Consultant Radiologist" — maximally relevant
  expertise, near-maximum conformity pressure (consistent with Asch,
  1951), ecologically valid for medical imaging.
- **AI agent:** 1 × "AI Diagnostic System" — realistic (clinicians
  receive a single AI recommendation) and neutral label to avoid
  pre-existing attitude confounds.
- Human count is identical across `human` and `human_ai` conditions so
  the only difference between those conditions is the presence of the
  AI, not the number of human opinions.



*Incorporating **Signal Detection Theory (SDT)** will allow us to model if these social/AI factors shift the participant's **criterion** (bias) or their actual **sensitivity** ($d'$).*
