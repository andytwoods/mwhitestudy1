i am # CLAUDE.md

## Coding Guidelines

All coding standards and conventions are defined in `.junie/guidelines.md`. Follow these exactly.

## Project Specification

The full project specification (study design, data requirements, trial flow, experimental conditions) is in `online_study_specification.md`.

## Project Overview

A Django web application for an online behavioural experiment investigating how human and AI feedback influences confidence and diagnostic judgements of medical images. Participants are recruited via Prolific Academic.

## Key Tech Stack

- **Backend:** Django, Python
- **CSS:** Bulma (no Bootstrap/Tailwind)
- **Dynamic UI:** HTMX (no React/Vue)
- **Auth:** django-allauth (Google + GitHub + email/password)
- **Background tasks:** Huey (never Celery)
- **Package manager:** `uv`
- **Forms:** crispy-forms with crispy-bulma
- **Modals/alerts:** SweetAlert2

## Settings

- `config/settings/base.py` — shared settings
- `config/settings/local.py` — local dev, uses SQLite
- `config/settings/production.py` — production, uses PostgreSQL + Rollbar error tracking

## Project Structure

- App templates live in `<app>/templates/<app>/` (not a global `templates/` directory)
- Base templates live in `pages/templates/`
- HTMX partials live in `<app>/templates/<app>/partials/` prefixed with `_`
