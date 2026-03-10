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

### Parameters captured

-   prolific_pid
-   prolific_study_id
-   prolific_session_id

### Additional stored data

-   entry_timestamp
-   completion_timestamp
-   completion_status

These parameters allow confirmation of completion and payment on
Prolific.

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

# Implementation Notes

The study will be implemented as a **Django web application**.

Core requirements:

-   capture Prolific parameters on entry
-   store consent and debrief HTML
-   support four within-subject conditions
-   configure trial counts via settings.py
-   randomise condition and trial order
-   load questions dynamically from database
-   record all responses
-   store configuration snapshots for reproducibility

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
The "Human" and "Human + AI" conditions require a logic for how external opinions are presented.
* **Quantity and Status**: We need to define the number of "other humans" shown. Notes suggest exploring if these humans are perceived as **"Professors"** (high expertise) or lower-quality raters, as this perception significantly alters how participants weigh the advice.
* **Consensus Modeling**: We must determine the **"Consensus of humans"** as an independent variable.
    * **High Consensus**: Multiple humans agreeing with each other.
    * **Low Consensus/Conflict**: Humans disagreeing, or the AI disagreeing with the human majority.
* **Bias Triggering**: We may intentionally introduce **"wrongness"** from the AI or humans — defined as feedback that is **opposite to the correct answer** (i.e. the feedback agent diagnoses malignant when the ground truth is benign, or vice versa). This allows us to observe how participant confidence shifts when faced with incorrect consensus.

  > **OPEN DECISION:** How to treat "wrongness" trials in the analysis is unresolved. Key questions include: Should incorrect-feedback trials be a separate factor? Should they be evenly distributed or sparse? How do they interact with consensus level? This will be revisited before implementation. See `study_recommendations.md` issue 5.



*Incorporating **Signal Detection Theory (SDT)** will allow us to model if these social/AI factors shift the participant's **criterion** (bias) or their actual **sensitivity** ($d'$).*
