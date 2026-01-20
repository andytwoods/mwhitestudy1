# Django Guidelines

You are an expert in Python, Django, and scalable web apps. Write secure, maintainable, performant code.

## Overview
- Research-focused Django application for behavioural / HCI-style studies.
- Participants arrive at a study-specific URL and are guided through:
- one or more case studies / vignettes; followed by questions after each case study (comprehension, judgement, decision-making, etc.).
- Primarily server-rendered, session-based flow; no requirement for real-time collaboration.
- Data integrity, reproducibility, and clean separation between stimuli, responses, and analysis outputs are first-order concerns.
- Monolithic Django app using Cookiecutter Django as the base skeleton; optimise for clarity and auditability over premature abstraction.



## Python
- Follow PEP 8 (120 char limit), double quotes, `isort`, f-strings.

### Exception handling
- **Never use catch-all exceptions**:
  - Do not use bare `except:` or `except Exception:` anywhere in the codebase.
  - Always catch the **most specific** exception you can genuinely handle.
  - If meaningful recovery is not possible, let the exception propagate so it fails loudly.
  - Use logging instead of `print()` when reporting errors.
- **Static analysis**
  - Configure linting (e.g. Ruff/flake8) to *error on*:
    - bare `except:`
    - `except Exception:`
    - unused exception variables

## Django
- Monolithic Django app using Cookiecutter Django as the base skeleton.
- Use built-ins before third-party; prefer established libraries to custom code.
- Server-rendered Django templates for core pages.
- Strong preference for HTMX for progressive enhancement and interactive UX (modals, inline edits, partial reloads) instead of building a separate SPA.
- API: Prefer Django Ninja; keep simple, versioned endpoints (DRF acceptable if warranted).
- Prioritise security; use ORM over raw SQL. Enforce permissions/roles on every view/endpoint.
- Absolutely no custom/raw SQL in app code or tests. Do not use connection.cursor(), QuerySet.extra(), QuerySet.raw(), or any
  hand-written SQL strings. Prefer Django ORM features (Q/F expressions, annotate, Subquery/Exists, Func/expressions,
  aggregations, window functions) and add appropriate indexes instead of raw SQL.
- Use signals sparingly.

### Project structure & Django apps
- Create separate Django apps when a bounded context emerges (e.g., users, tasks, matching, payments, notifications). Avoid dumping unrelated code into existing apps.
- How to create an app: `python manage.py startapp <app_name>` (snake_case, concise domain name). Add `<app_name>.apps.<AppConfig>` to `INSTALLED_APPS`.
- Each app must be self-contained and include, when applicable:
  - models.py with `__str__`, migrations (always use migrations).
  - admin.py registrations.
  - urls.py (namespaced with `app_name`), views.py, forms.py.
  - templates/<app_name>/... and static/<app_name>/... for namespacing.
  - tests/ package (pytest-style) colocated in the app.
  - tasks.py only for task wrappers, and helpers/task_helpers.py for task logic (see Tasks section).
- Wire app URLs from project urls.py using `path("<app_name>/", include("<app_name>.urls", namespace="<app_name>"))`.
- Keep cross-app coupling minimal. Share logic via explicit imports or a common utilities module when truly cross-cutting.
- Prefer a new app when:
  - The code has its own models and lifecycle.
  - It could be reused or turned off independently.
  - It introduces permissions/roles distinct from existing apps.
- Do not create a new app when the code is merely a small feature tightly coupled to an existing app’s data model.

## Models
- Always add `__str__`.
- Use `related_name` when helpful.
- `blank=True` for forms, `null=True` for DB.
- Use django-extensions' TimeStampedModel when appropriate.
- Use UUIDv7 for models that need to be globally unique.
- Prefer the **Event Sourcing pattern** for complex state (e.g., tasks, transactions): record immutable events (inserts) rather than overwriting state (updates) to preserve history and intent.

### Users model guidance
- **Prefer separate apps over bloating the Users model**. The Users app should focus on core authentication, profile, and account management.
- It's acceptable to add fields to the User model and a few related views when the functionality is truly core to user identity (e.g., profile fields, preferences).
- For domain-specific functionality (e.g., ratings, payments, subscriptions, achievements), create a separate Django app with its own models that relate to User via ForeignKey or OneToOneField.
- This keeps the Users app lean, maintains clear separation of concerns, and makes features easier to test, modify, or remove independently.

## Views
- Validate/sanitise input.
- Prefer `get_object_or_404`.
- Paginate lists.

## URLs
- Descriptive names, end with `/`.

## Forms
- Prefer ModelForms.
- Use crispy-forms (or similar).

## Templates
- Use inheritance.
- Extract reusable UI into Django template partials using `{% partialdef %}` to keep templates DRY and composable.
- Keep logic minimal.
- Always `{% load static %}`, enable CSRF.

## Settings
- Use env vars, never commit secrets (e.g., DB, Redis, VAPID keys for Web Push).

## Database
- PostgreSQL as the database.
- Always use migrations.
- Optimise queries (`select_related`, `prefetch_related`).
- Index frequent lookups.
- Never write custom/raw SQL in the codebase or in tests. Use the Django ORM exclusively.
- Migrations should be generated via makemigrations and use schema operations (AddField, AlterField, RunPython for data
  migrations implemented with the ORM). Avoid RunSQL entirely.

## Tasks (Framework-Agnostic)

### Task layout
- Each app’s `tasks.py` must **only** contain task-decorated functions for the chosen task-queue system.
- No business logic, utility functions, or classes should be placed in `tasks.py`.
- Task functions should:
  - accept and validate raw input;
  - call helper functions that contain the actual business logic;
  - handle only queue-specific concerns such as scheduling, retries, or metadata.

### Task helpers
- Create a dedicated module for task-related logic, e.g. `helpers/task_helpers.py` (project-wide or per-app).
- All business/domain logic used by tasks must live in `task_helpers.py`, not in `tasks.py`.
- Helper functions should be:
  - reusable by views, management commands, and tasks;
  - clear about side-effects;
  - written to be as idempotent as reasonably possible (safe for retries).

### Queue implementation
- Background tasks run with Huey + Redis.
- `tasks.py` should only wrap calls to helper functions and handle retry/scheduling concerns.

## Testing
- Write unit tests for new features.
- Cover both success and failure paths.
- Lean Startup: ship MVP, validate with small cohorts, iterate quickly.
- Agentic coding: when agents add important logic, include unit tests alongside changes (prefer test-first for core matching, geo, and notification flows).
- Tests must not execute raw SQL. Create, read, and assert using the ORM and factories/fixtures only. If an assertion seems
  to require SQL, refactor the production code to expose a testable interface or use ORM expressions/annotations to surface
  the needed data.

## Frontend PWA
- Ship as a PWA with a Service Worker (sw.js) responsible for:
  - Caching strategy (static assets + offline fallback page).
  - Receiving and displaying push notifications.
- Include push subscription bootstrap (push.js) using the Web Push API + Notifications API.
- UI via Bootstrap (latest version) for responsive, mobile-first design.
- **CSS & Styling**:
  - Preferentially use Bootstrap's default color scheme and utility classes (e.g., `text-primary`, `bg-light`, `btn-success`).
  - Use CSS variables and classes already defined in `static/css/project.css` before adding inline styles.
  - Only use inline styles or custom CSS when Bootstrap utilities and existing project styles cannot achieve the desired result.
  - Keep styling consistent across the application by reusing existing design tokens.

## Notifications (Web Push)
- Use open Web Push stack; preference for using Workbox established solutions
- Backend: pywebpush for encrypted payloads. Store VAPID private keys server-side via env vars.
- Persist per-user push subscriptions (endpoint, keys, UA hints, timestamps).
- Support iOS Safari PWA push and Android Chrome/Edge push.
- Security: validate subscription origins; rotate/handle invalid subscriptions; respect user opt-in/out.

## Location (≈20 m accuracy target)
- Obtain precise location via the Geolocation API only with explicit user permission.
- Use location to:
  - Match users and filter task feeds by proximity.
  - Support hyperlocal discovery and notifications for nearby tasks.
- Privacy & safety:
  - Ask permission contextually; explain purpose; allow revocation in account settings.
  - Store only what is necessary; consider rounding/gridding when full precision is not required.
  - Never expose exact coordinates to other users without explicit need/consent.

## Future Mobile Apps
- Native Android/iOS apps will be built later with Flutter, consuming the same Ninja API.
- The PWA is the MVP and the reference implementation; design APIs with this in mind.


