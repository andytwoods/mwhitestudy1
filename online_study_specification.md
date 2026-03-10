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

## Order Effects

Because block order is fully randomised, block position must be recorded
and included as a covariate in analysis (e.g. as a fixed effect in a mixed
model) to control for learning and fatigue effects that may be confounded
with condition order.

## Stored per participant

-   condition_order (the randomised sequence of condition blocks)
-   trial_order (the randomised trial sequence within each block)
-   image_assignment
-   block_position (numeric position 1–4 for each condition, for use as a
    covariate in analysis)

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
* **Bias Triggering**: We may intentionally introduce **"wrongness"** or "low likelihood" assessments from the AI or humans to observe how participant confidence shifts when faced with incorrect consensus or "intrigue".



*Incorporating **Signal Detection Theory (SDT)** will allow us to model if these social/AI factors shift the participant's **criterion** (bias) or their actual **sensitivity** ($d'$).*
