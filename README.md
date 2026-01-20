# MWhiteStudy1

MWhiteStudy1 is a research-focused Django application designed for behavioral and HCI-style studies. It guides participants through a staged flow of vignettes, content screens, and interactive questions using a seamless server-rendered experience powered by **HTMX**.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Getting Started

### Prerequisites

- **Python 3.12+**
- **uv** (recommended for dependency management)

### Local Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-repo/mwhitestudy1.git
    cd mwhitestudy1
    ```

2.  **Install dependencies:**

    We use `uv` to manage the environment and dependencies.

    ```bash
    uv sync --all-groups
    ```

3.  **Set up environment variables:**

    The project uses `django-environ`. You can create a `.env` file in the root directory for local development.

    ```bash
    cp .env.example .env  # If an example exists, otherwise create one
    ```

4.  **Run Migrations:**

    ```bash
    uv run python manage.py migrate
    ```

5.  **Create a Superuser:**

    ```bash
    uv run python manage.py createsuperuser
    ```

6.  **Run the Development Server:**

    ```bash
    uv run python manage.py runserver
    ```

    The site will be available at `http://127.0.0.1:8000/`.

## Running the Experiment

The core of the project is the `flow` app. You can access the demo study at:

`http://127.0.0.1:8000/s/demo/`

Participants progress through a sequence of screens defined in `mwhitestudy1/flow/study.py`.

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use the command mentioned in the Local Setup section.

### Type checks

Running type checks with mypy:

    uv run mypy mwhitestudy1

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    uv run coverage run -m pytest
    uv run coverage html
    uv run open htmlcov/index.html

#### Running tests with pytest

    uv run pytest

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Deployment

The following details how to deploy this application.
