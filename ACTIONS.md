# ACTIONS.md — Build Plan

Reference: `online_study_specification.md` (design), `.junie/guidelines.md` (coding standards).

---

## Implementation Contracts

Foundational decisions that every phase must follow. Resolve ambiguity before writing any code.

---

### URL Map

All participant-facing URLs are prefixed `/study/`. Each Django app owns its own `urls.py` with an `app_name` namespace. Wire into `config/urls.py` with `include()`.

| URL | View | Namespace:name | App |
|---|---|---|---|
| `/` | Landing / home | `pages:home` | `pages` |
| `/study/start/` | Prolific entry, session creation | `participants:entry` | `participants` |
| `/study/consent/` | Consent form | `participants:consent` | `participants` |
| `/study/questionnaire/background/` | Medical background form | `participants:background` | `participants` |
| `/study/questionnaire/ai-trust/` | AI trust scale (12 items) | `participants:ai-trust` | `participants` |
| `/study/trial/` | All trial stages (HTMX-driven) | `trials:trial` | `trials` |
| `/study/break/` | Inter-block break screen | `trials:block-break` | `trials` |
| `/study/post-study/` | Post-study measures | `participants:post-study` | `participants` |
| `/study/debrief/` | Debrief display | `participants:debrief` | `participants` |
| `/study/complete/` | Prolific redirect | `participants:complete` | `participants` |
| `/study/withdrawn/` | Withdrawal confirmation page | `participants:withdrawn` | `participants` |
| `/study/error/` | Parameter / eligibility error page | `participants:error` | `participants` |

`images` and `study` apps have no participant-facing URLs — researcher access is via Django admin only.

`config/urls.py` structure:
```python
urlpatterns = [
    path("", include("mwhitestudy1.pages.urls", namespace="pages")),
    path("study/", include("mwhitestudy1.participants.urls", namespace="participants")),
    path("study/", include("mwhitestudy1.trials.urls", namespace="trials")),
    path(settings.ADMIN_URL, admin.site.urls),
]
```

---

### Participant Session Guard

All views from `participants:consent` onward (inclusive) require an active participant session. Implement as a single mixin in `mwhitestudy1/participants/mixins.py`:

```python
class ParticipantSessionMixin:
    """
    Retrieves the active ParticipantSession from the Django session.
    Sets self.participant on the view. Redirects to entry on failure.
    """
    def dispatch(self, request, *args, **kwargs):
        participant_id = request.session.get("participant_id")
        if not participant_id:
            return redirect(reverse("participants:entry"))
        try:
            self.participant = ParticipantSession.objects.get(pk=participant_id)
        except ParticipantSession.DoesNotExist:
            return redirect(reverse("participants:entry"))
        if self.participant.completion_status == "complete":
            return redirect(reverse("participants:complete"))
        return super().dispatch(request, *args, **kwargs)
```

- Session key is always the string `"participant_id"`.
- `self.participant` is available in every protected view's `get()` and `post()` methods.
- `ParticipantSession.pk` (integer) is what is stored in the session — not the Prolific PID.
- Every class-based view in `participants` (except `entry` and `error`) and all views in `trials` inherit this mixin as their first base class.

---

### JSON Field Schemas

These schemas are fixed. Deviating from them will break the export command and tests.

#### `Trial.feedback_presented`

Stores a snapshot of exactly what was shown to the participant. `null` for baseline trials.

```json
{
  "agents": [
    {
      "agent_type": "human",
      "label": "Consultant Radiologist",
      "diagnosis": "malignant",
      "confidence": 0.85,
      "feedback_item_id": 42
    },
    {
      "agent_type": "human",
      "label": "Consultant Radiologist",
      "diagnosis": "malignant",
      "confidence": 0.91,
      "feedback_item_id": 57
    }
  ],
  "consensus": "unanimous",
  "accuracy": "correct"
}
```

- `agents` — one object per agent shown; length matches `FeedbackAgentDefinition.count` for the condition.
- `consensus` — always `"unanimous"` in study 1; stored for future studies.
- `accuracy` — `"correct"` or `"wrong"`, mirrors `Trial.feedback_accuracy`.
- `feedback_item_id` — FK to the `FeedbackItem` row sampled; enables audit trail.

#### `ParticipantSession.condition_order`

Ordered list of condition name strings in the randomised block sequence assigned to this participant.

```json
["baseline", "human_ai", "ai", "human"]
```

- Always length 4 (one entry per condition).
- Values are the condition `name` field values (`"baseline"`, `"human"`, `"human_ai"`, `"ai"`).
- Index 0 = block 1 (first block presented); index 3 = block 4.

#### `PreStudyMeasure.ai_trust_items`

Raw Likert responses to the 12-item Jian et al. scale, keyed by item number as a string.

```json
{
  "1": 5,
  "2": 3,
  "3": 6,
  "4": 4,
  "5": 7,
  "6": 2,
  "7": 5,
  "8": 4,
  "9": 3,
  "10": 6,
  "11": 5,
  "12": 4
}
```

- Keys `"1"` through `"12"` (strings, not integers).
- Values are integers in range 1–7 inclusive.
- `ai_trust_pre_score` is computed as `mean(values)` rounded to 4 decimal places.

---

### Consent and Debrief HTML Storage

Consent and debrief HTML is stored directly on the `Study` model — not a separate model. Add these fields to `Study`:

```python
consent_html = models.TextField()
consent_version = models.CharField(max_length=20)
debrief_html = models.TextField()
debrief_version = models.CharField(max_length=20)
```

The researcher edits this HTML via Django admin. The `Study` admin should use a `Textarea` widget with sufficient rows for comfortable editing.

At the point of presentation:
- `ConsentRecord` snapshots `study.consent_html` and `study.consent_version` into its own fields.
- `DebriefRecord` snapshots `study.debrief_html` and `study.debrief_version` into its own fields.

This ensures the exact HTML seen by each participant is preserved even if the researcher later edits the study's HTML.

---

### `import_feedback_data` CSV Schema

The CSV passed to the management command must have exactly these columns (header row required):

| Column | Type | Constraints |
|---|---|---|
| `image_external_id` | string | Must match an existing `Image.external_id` |
| `agent_type` | string | Must be `human` or `ai` |
| `diagnosis` | string | Must be `malignant` or `benign` |
| `confidence` | float | Range 0.0–1.0 inclusive |
| `source_label` | string | Free text, max 100 chars (e.g. `"Consultant Radiologist"`) |

Rows that fail validation are skipped and logged (not raised as exceptions), so a partial import can succeed. The command prints a summary: `Imported: N, Skipped: M` on completion.

---

### Practice Block Flow

Practice trials are served by the same `/study/trial/` view and `trials:trial` URL as real trials. No separate URL or view.

The `get_current_trial()` helper resolves practice trials first:

```python
Trial.objects.filter(participant=participant, ...).order_by(
    "-is_practice",   # practice trials sort before real trials
    "block_position",
    "trial_position",
)
```

After the last practice trial's responses are saved, the view returns a special `_practice_complete.html` partial (not the standard inter-trial partial). This partial displays a "Practice complete — the main study is about to begin" message and a "Start" button that loads the first real trial.

Practice trials have `block_position=0` and `trial_position` numbered from 1. They are never shown in the inter-block break progress indicator.

---

### Model Field Conventions

Apply these rules consistently across all models to avoid agent-level guessing:

| Field type | `null` | `blank` | Notes |
|---|---|---|---|
| `CharField` / `TextField` required | `False` | `False` | Default |
| `CharField` / `TextField` optional | `False` | `True` | Empty string, not NULL |
| `JSONField` optional | `True` | `True` | e.g. `feedback_presented` on baseline trials |
| `FloatField` / `IntegerField` optional | `True` | `True` | e.g. `median_trial_rt` before completion |
| `DateTimeField` optional | `True` | `True` | e.g. `completion_timestamp` |
| `BooleanField` | `False` | `False` | Always supply `default=` |
| `ForeignKey` | `False` | `False` | Unless explicitly nullable |

`max_length` defaults unless otherwise stated:
- Short identifiers / codes / slugs: `max_length=50`
- Labels / names / choices: `max_length=100`
- Version strings: `max_length=20`
- Free-text fields that may be long: use `TextField` (no `max_length`)

Index these fields (add `db_index=True`):
- `ParticipantSession.prolific_pid`
- `ParticipantSession.django_session_key`
- `ParticipantSession.completion_status`
- `Trial.block_position`
- `Trial.trial_position`
- `Trial.is_practice`
- `Response.stage_location`
- `Image.external_id` (also `unique=True`)

---

### Factory-Boy Factories

Create `<app>/tests/factories.py` in each app. Minimum required factories for Phase 10 integration test:

| Factory | App | Key traits |
|---|---|---|
| `StudyFactory` | `study` | Generates valid `config_json`; `is_active=True` |
| `ConditionFactory` | `study` | Linked to `StudyFactory`; `name` cycles through the 4 values |
| `FeedbackAgentDefinitionFactory` | `study` | Linked to `ConditionFactory` |
| `ParticipantSessionFactory` | `participants` | Valid Prolific params; `completion_status="in_progress"` |
| `ConsentRecordFactory` | `participants` | `consent_given=True`; linked to participant |
| `ImageFactory` | `images` | Alternates `ground_truth`; `is_practice=False` |
| `PracticeImageFactory` | `images` | `is_practice=True` trait on `ImageFactory` |
| `FeedbackItemFactory` | `trials` | Linked to `ImageFactory`; valid `agent_type` and `diagnosis` |
| `QuestionFactory` | `trials` | `is_active=True`; `stage_location` and `question_type` parameterised |
| `TrialFactory` | `trials` | Linked to participant, condition, image; `is_practice=False` |
| `ResponseFactory` | `trials` | Linked to trial, question; valid `response_value` |

---

## Phase 0 — Project Housekeeping ✓ COMPLETE

Fix mismatches between the existing scaffold and project requirements before any feature work begins.

### 0.1 Replace crispy-bootstrap5 with crispy-bulma
- Remove `crispy-bootstrap5` from `pyproject.toml` dependencies.
- Add `crispy-bulma` via `uv add crispy-bulma`.
- In `config/settings/base.py`: change `CRISPY_TEMPLATE_PACK` to `"bulma"` and `CRISPY_ALLOWED_TEMPLATE_PACKS` to `"bulma"`. Remove `crispy_bootstrap5` from `INSTALLED_APPS`, add `crispy_bulma`.
- Audit any existing form templates for Bootstrap-specific markup; replace with Bulma equivalents.

### 0.2 Add frontend JS dependencies (self-hosted)
- Download and place in `mwhitestudy1/static/js/`:
  - `htmx.min.js`
  - `sweetalert2.min.js`
- Download and place in `mwhitestudy1/static/css/`:
  - `bulma.min.css`
  - `sweetalert2.min.css`
- Remove any CDN references for these libraries from templates.

### 0.3 Create the `pages` app and migrate base templates
- Create `mwhitestudy1/pages/` Django app.
- Move `mwhitestudy1/templates/base.html` and shared partials to `pages/templates/`.
- Update `TEMPLATES["DIRS"]` in `base.py` to point to `pages/templates/` instead of the global templates dir.
- Register `mwhitestudy1.pages` in `INSTALLED_APPS`.
- Ensure `base.html` loads Bulma, HTMX, and SweetAlert2 from static files.

### 0.4 Delete the empty `flow` app
- Remove `mwhitestudy1/flow/` entirely (it contains no Python files).
- Remove any reference to it from `INSTALLED_APPS` or `config/urls.py`.

### 0.5 Create the four feature apps
Create the following Django apps under `mwhitestudy1/`:

| App | Responsibility |
|---|---|
| `study` | Study model, JSON config loading, Condition definitions, FeedbackAgent definitions |
| `participants` | ParticipantSession, consent/debrief records, pre/post measures, attention checks |
| `images` | Image bank, per-participant image assignment tracking |
| `trials` | Question, Trial, Response models; feedback pool; trial flow views |

For each app:
- `python manage.py startapp <name> mwhitestudy1/<name>`
- Register in `INSTALLED_APPS` as `"mwhitestudy1.<name>"`.
- Create `mwhitestudy1/<name>/templates/<name>/` and `partials/` subdirectory.
- Add an empty `urls.py` and wire into `config/urls.py`.

### 0.6 Add `study_configs/` directory
- Create `study_configs/` at project root.
- Add `study_configs/study1.json` populated with the agreed config from the spec (baseline/human/human_ai/ai trial counts, wrongness rate 0.25, consensus unanimous, agent definitions).
- Add `ACTIVE_STUDY_CONFIG = "study_configs/study1.json"` to `config/settings/base.py`.

---

## Phase 1 — Core Data Models ✓ COMPLETE

Define all models before writing any views. Run migrations after each app.

### 1.1 `study` app models

**`Study`**
- `name`, `slug` (unique)
- `config_json` (JSONField) — full contents of the active JSON config at study creation time
- `is_active` (bool)
- `created_at`

**`Condition`**
- `study` (FK → Study)
- `name` (choices: baseline / human / human_ai / ai)
- `display_order`

**`FeedbackAgentDefinition`**
- `condition` (FK → Condition)
- `agent_type` (choices: human / ai)
- `label` (e.g. "Consultant Radiologist")
- `count` (number of independent assessments shown)

Register all in `study/admin.py`.

### 1.2 `participants` app models

**`ParticipantSession`**
- `study` (FK → Study)
- `prolific_pid`, `prolific_study_id`, `prolific_session_id`
- `ip_address`
- `django_session_key` (links to Django session)
- `entry_timestamp`, `completion_timestamp`
- `completion_status` (choices: in_progress / complete / partial)
- `condition_order` (JSONField — randomised list of condition names)
- `study_version` (snapshot of `Study.config_json` at session start)
- `excluded_inattentive` (bool, default False)
- `attention_checks_failed` (int, default 0)
- `median_trial_rt` (float, nullable)

**`ConsentRecord`**
- `participant` (OneToOne → ParticipantSession)
- `consent_html`, `consent_version`
- `consent_given` (bool)
- `consent_timestamp`

**`DebriefRecord`**
- `participant` (OneToOne → ParticipantSession)
- `debrief_html`, `debrief_version`
- `debrief_timestamp`

**`PreStudyMeasure`**
- `participant` (OneToOne → ParticipantSession)
- `medical_training_level` (choices per spec)
- `ai_trust_pre_score` (float — mean of 12 Jian et al. items)
- Raw item responses stored as JSONField (`ai_trust_items`)

**`PostStudyMeasure`**
- `participant` (OneToOne → ParticipantSession)
- `noticed_feedback` (choices: yes / no / unsure)
- `attention_to_feedback` (int 1–7)
- `influence_of_feedback` (int 1–7)
- `demand_awareness_response` (TextField — open-ended verbatim)
- `demand_awareness_coded` (int 0/1/2, nullable — coded post-hoc)

**`AttentionCheckResponse`**
- `participant` (FK → ParticipantSession)
- `check_number` (int: 1, 2, or 3)
- `check_type` (choices: imc / catch_trial / infrequency)
- `response_value` (CharField)
- `passed` (bool)

Register all in `participants/admin.py`.

### 1.3 `images` app models

**`Image`**
- `external_id` (unique slug — from source dataset)
- `ground_truth` (choices: malignant / benign)
- `image_file` (ImageField → `media/images/`)
- `is_practice` (bool — practice images excluded from main bank)
- `is_catch_trial` (bool — unambiguous images designated for check 2)
- `source_dataset` (CharField)
- `uploaded_at`

**`ImageAssignment`** (tracks per-participant allocation for balance)
- `image` (FK → Image)
- `participant` (FK → ParticipantSession)
- `condition` (FK → Condition)
- Used to enforce: no repeats per participant; roughly equal image distribution across conditions across all participants.

Register all in `images/admin.py` with list filters for `ground_truth`, `is_practice`, `is_catch_trial`.

### 1.4 `trials` app models

**`Question`** (database-driven question system)
- `study` (FK → Study)
- `question_text`
- `question_type` (choices: multiple_choice / likert / slider / binary / numeric / free_text)
- `response_options` (JSONField — null for free text/numeric)
- `scale_min`, `scale_max`, `scale_step` (for slider/numeric)
- `condition_applicability` (JSONField — list of condition names, empty = all)
- `stage_location` (choices: pre_trial / initial_judgement / post_feedback / post_trial / end_of_study)
- `display_order` (int)
- `is_active` (bool)

**`FeedbackItem`** (pool of real human response data imported per image)
- `image` (FK → Image)
- `agent_type` (choices: human / ai)
- `diagnosis` (choices: malignant / benign)
- `confidence` (float)
- `source_label` (e.g. "Consultant Radiologist")
- `imported_at`

**`Trial`**
- `participant` (FK → ParticipantSession)
- `condition` (FK → Condition)
- `image` (FK → Image)
- `image_ground_truth` (copied at assignment time — denormalised for analysis)
- `block_position` (int 1–4 — position of this condition block in participant's order)
- `trial_position` (int — position within block)
- `is_practice` (bool)
- `is_catch_trial` (bool)
- `feedback_presented` (JSONField — snapshot of feedback shown, nullable for baseline)
- `feedback_accuracy` (choices: correct / wrong / na — na for baseline)
- `feedback_consensus_level` (CharField)
- `created_at`

**`Response`**
- `participant` (FK → ParticipantSession)
- `trial` (FK → Trial)
- `question` (FK → Question)
- `response_value` (CharField — all types stored as string; cast on analysis)
- `response_timestamp`
- `stage_location` (mirrors Question.stage_location — denormalised for query efficiency)

Register all in `trials/admin.py`.

---

## Phase 2 — Study Configuration Loading ✓ COMPLETE

### 2.1 Config loader utility
- Create `mwhitestudy1/study/helpers/config_loader.py`.
- `load_active_study_config() -> dict`: reads `settings.ACTIVE_STUDY_CONFIG`, parses JSON, returns dict.
- `get_or_create_active_study() -> Study`: loads config, creates or retrieves `Study` record, stores `config_json` snapshot.
- Used at startup (management command) and in session initialisation.

### 2.2 Management command: `bootstrap_study`
- `mwhitestudy1/study/management/commands/bootstrap_study.py`
- Calls `get_or_create_active_study()`.
- Creates `Condition` and `FeedbackAgentDefinition` records from the JSON config.
- Creates `Question` records for the active study (initial set loaded from a fixture or inline definition).
- Idempotent — safe to re-run.

### 2.3 Management command: `import_feedback_data`
- `mwhitestudy1/trials/management/commands/import_feedback_data.py`
- Accepts a CSV/JSON file path as argument.
- Imports real human/AI response data into `FeedbackItem` for each image.
- Validates: image must exist in `Image` table; agent_type and diagnosis must be valid choices.
- Reports counts of imported vs skipped rows.

---

## Phase 3 — Image Bank Management ✓ COMPLETE

### 3.1 Image upload via Django admin
- Customise `images/admin.py` with `ImageAdmin`:
  - List display: `external_id`, `ground_truth`, `is_practice`, `is_catch_trial`, `source_dataset`
  - List filters: `ground_truth`, `is_practice`, `is_catch_trial`
  - Search: `external_id`, `source_dataset`
- No custom views needed — Django admin is sufficient for researcher image management.

### 3.2 Management command: `import_images`
- `mwhitestudy1/images/management/commands/import_images.py`
- Accepts a directory path and a metadata CSV (columns: `external_id`, `ground_truth`, `is_practice`, `is_catch_trial`, `source_dataset`).
- Creates `Image` records and copies files to `MEDIA_ROOT/images/`.
- Idempotent on `external_id`.

### 3.3 Image assignment helper
- `mwhitestudy1/images/helpers/assignment.py`
- `assign_images_to_participant(participant, study_config) -> dict[condition_name, list[Image]]`
  - Queries `ImageAssignment` to find the current assignment counts per image per condition across all participants.
  - Samples from the image bank using a weighted random draw (lower-assigned images preferred) to achieve approximate balance.
  - Enforces: equal malignant/benign split per condition; no image repeats per participant.
  - Writes `ImageAssignment` records.
  - Returns a mapping of condition → assigned image list.
- Unit-testable in isolation (no view dependencies).

---

## Phase 4 — Participant Entry & Consent ✓ COMPLETE

### 4.1 Entry view
- URL: `/study/start/`
- Captures `PROLIFIC_PID`, `STUDY_ID`, `SESSION_ID` from query params.
- Validates: all three params present; `PROLIFIC_PID` not already `completion_status=complete` for the active study.
- Creates `ParticipantSession` (status: in_progress) and stores `session_key`.
- Stores `participant_id` in Django session.
- Redirects to consent view.
- If params missing: renders a clear error page (not an exception).

### 4.2 Consent view
- URL: `/study/consent/`
- GET: renders consent HTML (loaded from `ConsentRecord`-related study field or a DB-stored HTML blob).
- POST (HTMX): records `ConsentRecord` (html snapshot, version, timestamp, `consent_given`).
  - If `consent_given=False`: end session, show withdrawal page.
  - If `consent_given=True`: redirect to pre-study questionnaire.
- Template: `participants/templates/participants/consent.html`
- Partial: `participants/templates/participants/partials/_consent_form.html`

### 4.3 Pre-study questionnaire views
Two sequential pages:

**Medical background** (`/study/questionnaire/background/`)
- Single crispy-bulma form: medical training level (radio buttons styled as Bulma radio group).
- POST saves to `PreStudyMeasure.medical_training_level`.

**AI trust scale** (`/study/questionnaire/ai-trust/`)
- 12-item Jian et al. scale rendered as Likert rows (1–7).
- Each item is a Bulma field with radio buttons.
- POST: saves raw items to `ai_trust_items` JSONField, computes mean → `ai_trust_pre_score`.
- On completion: redirect to practice block.

---

## Phase 5 — Session Initialisation & Trial Generation

Runs once per participant immediately after pre-study questionnaires complete.

### 5.1 Session initialiser helper
- `mwhitestudy1/trials/helpers/session_init.py`
- `initialise_participant_session(participant) -> None`
  1. Randomise condition block order → store in `ParticipantSession.condition_order`.
  2. Call `assign_images_to_participant()` to get image lists per condition.
  3. For each condition block (in randomised order):
     - Randomise trial order within the block.
     - Create `Trial` records (is_practice=False) with `block_position`, `trial_position`, `image`, `image_ground_truth`, `condition`.
     - Determine `feedback_accuracy` for each trial: sample from wrongness rate config (25% wrong, 75% correct), ensuring equal distribution of wrong trials within the block.
     - Select `FeedbackItem` records for each trial: sample from the pool matching the required diagnosis (correct or wrong) and agent types per condition config. Store snapshot in `Trial.feedback_presented`.
  4. Create practice `Trial` records (is_practice=True) using practice images, with one example of each question type.
  5. Embed attention check trials at specified positions (check 1 in first block, check 2 as catch trial in mid-study block).
- Called synchronously from the post-questionnaire view. No background task required.

---

## Phase 6 — Trial Flow (Core)

All trial stage transitions use HTMX partial swaps. The view always resolves `next_trial` or `next_stage` from session state — there is no client-side trial logic.

### 6.1 Trial state helper
- `mwhitestudy1/trials/helpers/trial_state.py`
- `get_current_trial(participant) -> Trial | None`: finds the next incomplete trial ordered by `block_position`, `trial_position`.
- `get_current_stage(participant, trial) -> str`: returns the stage the participant is at for a given trial (initial_judgement / post_feedback / complete), inferred from which `Response` records exist.

### 6.2 Trial view (single URL, HTMX-driven)
- URL: `/study/trial/`
- View resolves current trial and stage via helpers.
- GET: full page render for first load; HTMX request returns partial only.
- Same-endpoint pattern — no separate URLs per stage.
- Stages handled within the same view:

**Stage 1 — Initial judgement** (`partials/_stage_initial.html`)
- Shows the medical image (full width on mobile, left column on ≥tablet).
- Right column: crispy-bulma forms for `initial_judgement`-stage questions (diagnosis binary + confidence slider).
- On submit (HTMX POST): saves `Response` records with timestamp. Returns stage 2 partial if condition ≠ baseline; returns stage 3 partial if baseline.

**Stage 2 — Feedback display** (`partials/_stage_feedback.html`)
- Image remains visible.
- Feedback cards rendered from `Trial.feedback_presented` snapshot.
- Each agent gets a Bulma card: label, diagnosis badge, confidence bar.
- Multiple cards wrap in Bulma columns.
- For baseline: this stage is skipped entirely.
- No user input on this partial — a "Continue" button triggers HTMX swap to stage 3.

**Stage 3 — Post-feedback questions** (`partials/_stage_post_feedback.html`)
- Crispy-bulma forms for `post_feedback`-stage questions (updated diagnosis, updated confidence, trust in feedback, perceived usefulness).
- On submit (HTMX POST): saves `Response` records with timestamp. Returns inter-trial partial.

**Inter-trial / inter-block** (`partials/_inter_trial.html`, `partials/_inter_block.html`)
- Inter-trial: minimal "Next image →" button.
- Inter-block: mandatory break screen with progress indicator (e.g. "Block 2 of 4 complete") and "Continue" button. Participant must actively dismiss before next block loads.
- SweetAlert2 used only for unexpected errors or session expiry warnings.

### 6.3 Response saving
- All response saves go through `mwhitestudy1/trials/helpers/response_save.py`.
- `save_response(participant, trial, question, value, stage) -> Response`
  - Validates: question is active; question applies to the trial's condition; stage matches.
  - Records `response_timestamp = now()`.
  - Returns the saved `Response`.

### 6.4 RT tracking
- Each stage partial includes a hidden `stage_start_time` field (ISO timestamp set by inline JS when partial renders).
- Submitted with each POST. Stored on `Response` as `client_rt_ms` (int, nullable).
- Used to compute `ParticipantSession.median_trial_rt` at completion.

---

## Phase 7 — Attention Checks

### 7.1 IMC (check 1)
- A `Question` record with `question_type=multiple_choice` and embedded instruction in `question_text`.
- Placed at `stage_location=post_trial`, `display_order` = first trial of block 1.
- After saving the response, check logic in `mwhitestudy1/participants/helpers/attention.py`:
  - `evaluate_attention_check(participant, check_number, response_value) -> bool`
  - Increments `ParticipantSession.attention_checks_failed` if failed.
  - Creates `AttentionCheckResponse` record.

### 7.2 Catch trial (check 2)
- One `Image` with `is_catch_trial=True` is included in the mid-study block.
- `Trial.is_catch_trial=True` flagged at session init.
- After initial judgement response is saved, evaluate against `image_ground_truth`.
- If incorrect: call `evaluate_attention_check(participant, 2, response_value)`.

### 7.3 Infrequency item (check 3, optional)
- A `Question` record at `stage_location=end_of_study`.
- Evaluated in `evaluate_attention_check(participant, 3, response_value)`.

### 7.4 Exclusion flag
- After check 3 (or at study completion), if `attention_checks_failed >= 2`: set `ParticipantSession.excluded_inattentive = True`.

---

## Phase 8 — Post-Study & Completion

### 8.1 Post-study measures view
- URL: `/study/post-study/`
- Three sequential crispy-bulma forms (can be one page, stacked, with HTMX progression):
  1. Manipulation check (noticed feedback, attention to feedback, influence of feedback).
  2. Infrequency item (attention check 3).
  3. Demand awareness (open-ended text, shown last to avoid priming).
- All saved to `PostStudyMeasure`.

### 8.2 Debrief view
- URL: `/study/debrief/`
- Renders debrief HTML from DB (stored on `Study` model or a separate `DebriefContent` model).
- On render: creates `DebriefRecord` (html, version, timestamp).
- Sets `ParticipantSession.completion_status = "complete"` and `completion_timestamp = now()`.
- Computes and stores `median_trial_rt` from all `Response.client_rt_ms` values for the participant.
- Renders Prolific redirect button (not auto-redirect — participant clicks).

### 8.3 Prolific redirect
- URL: `/study/complete/`
- Reads `PROLIFIC_COMPLETION_CODE` from active study config.
- Redirects to `https://app.prolific.com/submissions/complete?cc=<code>`.
- Guard: only reachable if `completion_status = "complete"`.

### 8.4 Partial completion handling
- Middleware or mixin on all trial/study views: if session has no `participant_id` or session has expired, redirect to a "session expired" page (not the start URL — avoids duplicate entries).
- If participant abandons (detected by session expiry or explicit withdrawal): `completion_status` remains `in_progress` and is set to `partial` by a nightly management command `mark_partial_sessions` (marks sessions older than 2 hours with status in_progress as partial).

---

## Phase 9 — Admin & Researcher Interface

### 9.1 Django admin enhancements
All models registered with appropriate `list_display`, `list_filter`, `search_fields`, and `readonly_fields`.

Key additions:
- `ParticipantSession` admin: filter by `completion_status`, `excluded_inattentive`; show `attention_checks_failed`, `median_trial_rt`.
- `Trial` admin: filter by `condition`, `feedback_accuracy`, `is_practice`, `is_catch_trial`.
- `Response` admin: filter by `stage_location`; link to trial and participant.
- `FeedbackItem` admin: filter by `agent_type`, image `ground_truth`.
- `Question` admin: filter by `stage_location`, `condition_applicability`, `is_active`; preserve `display_order` ordering.

### 9.2 Data export management command
- `mwhitestudy1/trials/management/commands/export_study_data.py`
- Exports to CSV: one row per `Response`, joined with trial, participant, image, and condition fields needed for the GLMM.
- Columns: `participant_id`, `prolific_pid`, `condition`, `block_position`, `trial_position`, `image_id`, `image_ground_truth`, `feedback_accuracy`, `question_id`, `stage_location`, `response_value`, `response_timestamp`, `client_rt_ms`, `medical_training_level`, `ai_trust_pre_score`, `excluded_inattentive`, `completion_status`.

---

## Phase 10 — Testing

One test module per app. Tests live in `<app>/tests/`. Every test case states its **action**, **expected result**, and **pass criterion** explicitly.

### Conventions
- Use `pytest-django` with `@pytest.mark.django_db`.
- Use `factory_boy` factories for all model creation — no raw `Model.objects.create()` in test bodies.
- Never hard-code URL paths; use `reverse()`.
- Cover both the success path and the primary failure path for every behaviour.
- A test passes only if the assertion matches exactly — no "approximately correct" assertions except where statistical behaviour is explicitly noted.

---

### 10.1 `study` app tests

#### Config loader (`test_config_loader.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 1 | Call `load_active_study_config()` with a valid JSON path | Returns a dict with keys `study_id`, `trials_per_condition`, `feedback_wrong_rate` | `isinstance(result, dict)` and all three keys present |
| 2 | Call with a path to a non-existent file | Raises `FileNotFoundError` | `pytest.raises(FileNotFoundError)` |
| 3 | Call with a path to a syntactically invalid JSON file | Raises `json.JSONDecodeError` | `pytest.raises(json.JSONDecodeError)` |
| 4 | Call `get_or_create_active_study()` twice with the same config | Returns the same `Study` record both times; no duplicate created | `Study.objects.count() == 1` after two calls |

#### `bootstrap_study` command (`test_bootstrap_study.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 5 | Run `bootstrap_study` once against a valid config | Creates one `Study`, one `Condition` per condition key, `FeedbackAgentDefinition` rows matching agent config | Counts match config; no exception raised |
| 6 | Run `bootstrap_study` a second time | No duplicate models created | Counts unchanged from after run 1 |
| 7 | Run with a config missing `trials_per_condition` | Raises a descriptive `KeyError` or `ValueError` before writing to DB | DB unchanged; error raised |

---

### 10.2 `participants` app tests

#### Entry view (`test_entry.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 8 | GET `/study/start/` with all three Prolific params present | `ParticipantSession` created; session contains `participant_id`; redirects to consent | `ParticipantSession.objects.count() == 1`; response status 302 to consent URL |
| 9 | GET `/study/start/` with `PROLIFIC_PID` missing | Renders error page (not a 500) | Response status 200; no `ParticipantSession` created |
| 10 | GET `/study/start/` with a PID that already has `completion_status=complete` | Renders rejection page | Response status 200; no new `ParticipantSession` created |
| 11 | GET `/study/start/` with a PID that has `completion_status=partial` | Creates a new session (re-entry allowed for partial) | `ParticipantSession.objects.filter(prolific_pid=pid).count() == 2` |

#### Consent view (`test_consent.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 12 | POST consent with `consent_given=True` | `ConsentRecord` created with correct html/version/timestamp; redirects to background questionnaire | `ConsentRecord.consent_given == True`; response 302 |
| 13 | POST consent with `consent_given=False` | `ConsentRecord` created with `consent_given=False`; renders withdrawal page; session not progressed | `ConsentRecord.consent_given == False`; no `PreStudyMeasure` created |
| 14 | GET consent with no `participant_id` in session | Redirects to entry URL | Response status 302 to `/study/start/` |

#### Pre-study questionnaires (`test_questionnaires.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 15 | POST AI trust scale with all 12 items in range 1–7 | `PreStudyMeasure` created; `ai_trust_pre_score` equals mean of submitted values (to 4 d.p.) | `abs(record.ai_trust_pre_score - expected_mean) < 0.0001` |
| 16 | POST AI trust scale with one item value of 0 (out of range) | Form invalid; no `PreStudyMeasure` created | Response re-renders form; `PreStudyMeasure.objects.count() == 0` |
| 17 | POST AI trust scale with one item value of 8 (out of range) | Form invalid; no `PreStudyMeasure` created | Response re-renders form; `PreStudyMeasure.objects.count() == 0` |
| 18 | POST medical background with a valid `medical_training_level` | `PreStudyMeasure.medical_training_level` saved correctly | Field value matches submitted choice |

---

### 10.3 `images` app tests

#### Assignment helper (`test_assignment.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 19 | Assign images to one participant (5 trials per condition, 10 malignant + 10 benign in bank) | No image appears in more than one condition for this participant | `len(set(all_assigned_image_ids)) == total_trials` |
| 20 | Assign images to one participant with 5 trials per condition | Each condition receives exactly equal malignant and benign counts | For each condition: `malignant_count == benign_count` |
| 21 | Assign images to 10 participants sequentially | Each image's assignment count across conditions does not diverge by more than 2 from the expected even distribution | `max_count - min_count <= 2` across all image-condition pairs |
| 22 | Call assignment when the bank has fewer images than required | Raises `ValueError` with message indicating insufficient images | `pytest.raises(ValueError)` |

#### `import_images` command (`test_import_images.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 23 | Run with a valid directory and metadata CSV | `Image` records created for each row; file exists at `MEDIA_ROOT/images/` | `Image.objects.count() == row_count` |
| 24 | Run a second time with the same CSV | No duplicate `Image` records created | Count unchanged |
| 25 | Run with a row where `ground_truth` is not `malignant` or `benign` | Raises `ValueError`; no records written for that row | Record for that `external_id` absent |

---

### 10.4 `trials` app tests

#### Session initialiser (`test_session_init.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 26 | Call `initialise_participant_session()` with config specifying 5 trials per condition | Exactly 20 non-practice `Trial` records created | `Trial.objects.filter(participant=p, is_practice=False).count() == 20` |
| 27 | Same call | `block_position` values are 1–4, each appearing exactly 5 times | `Counter(block_positions) == {1:5, 2:5, 3:5, 4:5}` |
| 28 | Same call | `trial_position` within each block runs 1–5 with no gaps or repeats | For each block: `sorted(positions) == [1,2,3,4,5]` |
| 29 | Simulate 100 participants | Proportion of trials with `feedback_accuracy=wrong` is between 0.20 and 0.30 for non-baseline conditions | `0.20 <= wrong_rate <= 0.30` |
| 30 | Same call | `condition_order` on `ParticipantSession` contains all 4 conditions exactly once | `sorted(condition_order) == sorted(all_condition_names)` |
| 31 | Call with no `FeedbackItem` records for a required image | Raises `ValueError` before creating any `Trial` | No `Trial` records created; error raised |

#### Trial state helper (`test_trial_state.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 32 | Call `get_current_trial()` for a participant with no responses | Returns the trial with `block_position=1`, `trial_position=1` | Returned trial matches expected pk |
| 33 | Call `get_current_trial()` after all trials have complete responses | Returns `None` | `result is None` |
| 34 | Call `get_current_stage()` with no responses on trial | Returns `"initial_judgement"` | `result == "initial_judgement"` |
| 35 | Call `get_current_stage()` after initial judgement responses saved but no post-feedback responses | Returns `"post_feedback"` | `result == "post_feedback"` |

#### Trial view (`test_trial_view.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 36 | GET `/study/trial/` with no `participant_id` in session | Redirects to `/study/start/` | Response status 302; location is entry URL |
| 37 | POST initial judgement for a non-baseline trial | Returns HTTP 200 with HTMX partial containing feedback cards | Response contains feedback agent label string |
| 38 | POST initial judgement for a baseline trial | Returns HTTP 200 with HTMX partial for post-feedback questions (feedback stage skipped) | Response does not contain feedback card markup |
| 39 | POST the same initial judgement twice | Second POST rejected | `Response.objects.filter(trial=t, stage_location="initial_judgement").count() == 1` after both POSTs |

#### Response saving (`test_response_save.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 40 | Call `save_response()` with valid inputs | `Response` created with non-null `response_timestamp` | `Response.objects.count() == 1`; `response_timestamp` is not None |
| 41 | Call `save_response()` for a question with `is_active=False` | Raises `ValueError` | No `Response` created |
| 42 | Call `save_response()` for a question whose `condition_applicability` excludes the trial's condition | Raises `ValueError` | No `Response` created |

#### Attention checks (`test_attention.py`)

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 43 | Call `evaluate_attention_check()` with correct response for check 1 | `AttentionCheckResponse.passed=True`; `attention_checks_failed` unchanged | `participant.attention_checks_failed == 0` |
| 44 | Call with wrong response for check 1 | `AttentionCheckResponse.passed=False`; `attention_checks_failed` incremented to 1 | `participant.attention_checks_failed == 1` |
| 45 | Fail checks 1 and 2 | `ParticipantSession.excluded_inattentive=True` | `participant.excluded_inattentive == True` |
| 46 | Fail only check 1 | `excluded_inattentive` remains False | `participant.excluded_inattentive == False` |

---

### 10.5 Integration test — full participant flow (`test_integration.py`)

Simulates one participant completing the entire study using the Django test client. Uses factory-boy to create a bootstrapped study, image bank, and feedback pool.

| # | Action | Expected result | Pass criterion |
|---|---|---|---|
| 47 | Complete all steps: entry → consent → questionnaires → practice → all trials → post-study → debrief | `completion_status = "complete"` | `ParticipantSession.completion_status == "complete"` |
| 48 | Same run | Correct total `Response` count (all questions × all applicable trials) | `Response.objects.filter(participant=p).count() == expected_total` |
| 49 | Same run | `ConsentRecord` and `DebriefRecord` both exist and are linked to the session | Both records queryable; `consent_given=True` |
| 50 | Same run | `median_trial_rt` is populated and is a positive float | `participant.median_trial_rt > 0` |
| 51 | Navigate to `/study/complete/` without having finished the study | Redirected away; Prolific completion URL not served | Response status 302; Prolific URL not in response content |

---

## Dependency on External Data

The following must be available before Phase 5 (session initialisation) can run end-to-end:

1. **Images** — at least one image per ground truth class imported via `import_images`.
2. **FeedbackItems** — real human response data imported via `import_feedback_data` for each image that will appear in a non-baseline condition.
3. **Study bootstrapped** — `bootstrap_study` management command run at least once.

Development and testing prior to Phase 5 can use factory-boy fixtures to create synthetic `Image` and `FeedbackItem` records.
