from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from .study import get_screen, get_next_key
from .models import Response, ScreenEvent
from .helpers import get_or_create_participant, get_or_create_progress

def start_study(request, study_slug):
    # For now we ignore study_slug as we only have one hardcoded study
    force_new = request.GET.get("participant") == "new"
    participant = get_or_create_participant(request, force_new=force_new)
    progress = get_or_create_progress(participant)

    screen_key = progress.current_screen_key
    screen = get_screen(screen_key)

    # Log render event
    ScreenEvent.objects.create(
        participant=participant,
        screen_key=screen_key,
        event_type="render"
    )

    return render(request, "flow/start.html", {
        "study_slug": study_slug,
        "screen": screen,
        "participant": participant,
    })

@require_GET
def get_screen_fragment(request, study_slug, screen_key):
    participant = get_or_create_participant(request)
    screen = get_screen(screen_key)
    if not screen:
        return HttpResponseBadRequest("Invalid screen key")

    # Update progress if it's a valid transition or resuming
    progress = get_or_create_progress(participant)
    progress.current_screen_key = screen_key
    progress.save()

    # Log render event
    ScreenEvent.objects.create(
        participant=participant,
        screen_key=screen_key,
        event_type="render"
    )

    return render(request, "flow/_screen.html", {
        "study_slug": study_slug,
        "screen": screen,
    })

@require_POST
def submit_answer(request, study_slug, screen_key):
    participant = get_or_create_participant(request)
    screen = get_screen(screen_key)
    if not screen:
        return HttpResponseBadRequest("Invalid screen key")

    questions = screen.get("questions", [])
    errors = {}
    answers = {}

    for q in questions:
        val = request.POST.get(q["id"], "").strip()
        answers[q["id"]] = val

        if q.get("required") and not val:
            errors[q["id"]] = "This field is required."
            continue

        if val:
            if q["type"] == "int":
                try:
                    val = int(val)
                except ValueError:
                    errors[q["id"]] = "Please enter a valid number."
            elif q["type"] == "likert":
                try:
                    val = int(val)
                except ValueError:
                    errors[q["id"]] = "Invalid selection."

    if errors:
        return render(request, "flow/_screen.html", {
            "study_slug": study_slug,
            "screen": screen,
            "errors": errors,
            "answers": answers,
        })

    # Save responses
    for q_id, val in answers.items():
        Response.objects.update_or_create(
            participant=participant,
            screen_key=screen_key,
            question_id=q_id,
            defaults={"value": val}
        )

    # Log submit event
    ScreenEvent.objects.create(
        participant=participant,
        screen_key=screen_key,
        event_type="submit"
    )

    # Advance progress
    next_key = get_next_key(screen_key)
    if next_key:
        progress = get_or_create_progress(participant)
        progress.current_screen_key = next_key
        progress.save()

        next_screen = get_screen(next_key)
        return render(request, "flow/_screen.html", {
            "study_slug": study_slug,
            "screen": next_screen,
        })
    else:
        # No next screen, we might be at the end
        return render(request, "flow/_screen.html", {
            "study_slug": study_slug,
            "screen": screen, # Re-render current (presumably "done" screen)
        })
