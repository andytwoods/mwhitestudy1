# Django + HTMX staged flow app – agent task sequence

## Target behaviour
- visitor opens a start URL
- they see a **screen**: optional image + text + a form with questions
- they submit answers
- backend records answers
- backend returns either:
  - the next screen immediately, or
  - an interstitial “press space to continue” screen (and sometimes multiple in a row), which loads the next screen via HTMX
- every screen transition is fetched from the backend via HTMX (partials)

---

## Task 0 – define the “screen” state machine
**Goal:** lock the data shape before coding templates/views.

**Deliverable:** a single Python dict (or DB rows later) describing a sequence of screens.

**Proposed screen schema (minimal):**
- `key` (string, unique)
- `kind`: `"content"` or `"continue"`
- `image_url` (optional, only for `content`)
- `text_html` (optional, only for `content`)
- `questions` (list, only for `content`)
- `next_key` (string or None)

**Question schema:**
- `id` (string, unique per study)
- `type`: `"mcq"` | `"text"` | `"int"` | `"likert"`
- `prompt_html`
- `required` (bool)
- `options` (for mcq/likert)

**Acceptance check:** you can express “text/questions, then continue, then more text/questions, then continue again” without hacks.

---

## Task 1 – create Django project + app
**Goal:** runnable local server.

**Steps**
- `django-admin startproject config .`
- `python manage.py startapp flow`
- add `flow` to `INSTALLED_APPS`

**Acceptance check:** server runs, app imports.

---

## Task 2 – base templates + HTMX wiring
**Goal:** a base layout and a single container that HTMX swaps.

**Deliverables**
- `templates/base.html` includes HTMX script
- `templates/flow/start.html` renders:
  - a `<main id="screen-root">` container
  - initial screen fragment included server-side (first load)

**Acceptance check:** page loads, shows the first screen without HTMX.

---

## Task 3 – minimal models for participants + responses
**Goal:** persist progress + answers.

**Models**
- `Participant` (uuid, created_at, user_agent, optional fields)
- `Progress` (participant FK, current_screen_key, updated_at)
- `Response` (participant FK, screen_key, question_id, value, created_at)

**Acceptance check:** migrate runs; you can create rows in shell.

---

## Task 4 – participant identification (cookie/session)
**Goal:** every visitor gets a stable participant uuid.

**Approach**
- on first request, create Participant + store uuid in session (or signed cookie)
- reuse thereafter

**Acceptance check:** refresh preserves participant id; new browser session creates a new one.

---

## Task 5 – study config loader
**Goal:** a single source of truth for the screen sequence.

**Deliverable**
- `flow/study.py` exporting `SCREENS = {...}` (dict keyed by `key`)
- helper functions:
  - `get_first_screen_key()`
  - `get_screen(key)`
  - `get_next_key(key)`

**Acceptance check:** you can fetch any screen by key and know the next key.

---

## Task 6 – render a screen fragment template
**Goal:** one partial that renders either content or continue.

**Deliverables**
- `templates/flow/_screen.html`
  - if `kind == "content"`: render image/text + `<form>`
  - if `kind == "continue"`: render “press space to continue” UI + an HTMX trigger element
- keep everything inside a wrapper `<section data-screen-key="...">`

**Acceptance check:** in a normal Django render, content and continue both look correct.

---

## Task 7 – URLs + views (start, screen fragment, submit)
**Goal:** server endpoints to support HTMX swaps.

**Endpoints**
- `GET /s/<study_slug>/` – start page (full HTML)
- `GET /s/<study_slug>/screen/<screen_key>/` – returns `_screen.html` partial
- `POST /s/<study_slug>/answer/<screen_key>/` – validates + stores answers, advances progress, returns next partial

**Acceptance check:** you can manually visit a screen fragment URL and see only the partial HTML.

---

## Task 8 – HTMX form submission
**Goal:** submitting answers swaps the screen in-place.

**Implementation**
- in `_screen.html` content form:
  - `hx-post` to `answer/<screen_key>/`
  - `hx-target="#screen-root"`
  - `hx-swap="innerHTML"`
- include CSRF token

**Acceptance check:** submit replaces the screen with the server’s returned next screen.

---

## Task 9 – validation + storage on submit
**Goal:** required questions enforced server-side.

**Implementation**
- parse POST using the `questions` spec
- for each question:
  - check required
  - coerce types (int/likert)
  - store `Response` rows (one per question)
- update `Progress.current_screen_key = next_key`

**Acceptance check:** missing required shows an error message in the fragment (no screen advance).

---

## Task 10 – continue screens advanced by spacebar
**Goal:** pressing space triggers an HTMX request to load the next screen.

**Implementation pattern**
- continue fragment includes a hidden button or div:
  - `hx-get="/s/<slug>/screen/<next_key>/"` (or a dedicated “advance” endpoint)
  - `hx-target="#screen-root"`
  - `hx-swap="innerHTML"`
  - `hx-trigger="advance"` (custom event)
- add a tiny JS file that:
  - listens for `keydown`
  - if key is Space and focus is not in an input/textarea/select/button
  - calls `htmx.trigger(document.body, "advance")` (or triggers the specific element)

**Acceptance check:** on continue screen, space advances; on text input, space types normally.

---

## Task 11 – support multiple continues in a row
**Goal:** “press space again” works repeatedly.

**Implementation**
- because continue screens are just screens with `kind="continue"` and `next_key`, no special casing needed
- progress updates when continue is served (either):
  - option a: update progress when returning the continue screen
  - option b: update progress only when advancing past it

**Recommendation:** option b – treat continue as a real screen key so refresh is stable.

**Acceptance check:** a sequence like `content -> continue -> continue -> content` works.

---

## Task 12 – refresh/back-button stability
**Goal:** user can refresh without breaking progression.

**Implementation**
- `GET /s/<slug>/` should render the participant’s `Progress.current_screen_key` (not always the first)
- optional: add `GET /s/<slug>/resume/` redirect to current screen

**Acceptance check:** refresh stays on the same screen.

---

## Task 13 – error rendering inside fragments
**Goal:** validation errors show nicely without leaving HTMX flow.

**Deliverables**
- fragment shows per-question error text
- keep previously entered values when re-rendering

**Acceptance check:** submit empty required field – error appears, values preserved where possible.

---

## Task 14 – basic styling and accessibility
**Goal:** clean, readable, keyboard-friendly.

**Deliverables**
- visible focus states
- labels properly linked to inputs
- continue screen clearly indicates “press space to continue”
- image has alt text (even if generic)

**Acceptance check:** tab order makes sense; screen readers get labels.

---

## Task 15 – admin-free “hardcoded study” working end-to-end
**Goal:** the first complete vertical slice without authoring UI.

**Deliverable**
- one study slug, e.g. `demo`
- at least:
  - screen 1 content (image+text+questions)
  - screen 2 continue
  - screen 3 content (text+questions)
  - screen 4 continue
  - screen 5 “done” content (no questions)

**Acceptance check:** start → answer → space → answer → space → done, with responses stored.

---

## Task 16 – automated tests (minimum viable)
**Goal:** prevent regressions.

**Tests**
- creates participant on first visit
- submitting valid answers advances progress
- submitting invalid answers does not advance
- continue screen advance endpoint swaps correctly

**Acceptance check:** `pytest` or Django test runner green.

---

## Task 17 – instrumentation (optional but usually worth it)
**Goal:** capture timestamps for each screen view + submit latency.

**Add**
- `ScreenEvent` model (participant, screen_key, event_type: `render`/`submit`/`advance`, ts)
- log events in fragment views + submit view

**Acceptance check:** you can reconstruct dwell time per screen.

---

## Task 18 – deployment-ready hygiene
**Goal:** production basics.

**Add**
- CSP considerations if text is HTML
- safe rendering (store text as trusted templates, or sanitise)
- settings for static files (whitenoise if desired)
- structured logging for responses

**Acceptance check:** can run with `DEBUG=False` locally.

---

## Suggested file layout
- `flow/models.py`
- `flow/study.py`
- `flow/views.py`
- `flow/urls.py`
- `templates/base.html`
- `templates/flow/start.html`
- `templates/flow/_screen.html`
- `static/flow/keys.js`

---

## Key design choice (make early)
**Do you want “continue” screens to be addressable (stable keys) or purely transient?**

Recommendation: implement them as normal screens with keys – it makes refresh/resume clean and makes “press space again” trivial.
