SCREENS = {
    "start": {
        "key": "start",
        "kind": "content",
        "text_html": "<h1>Welcome to the study</h1><p>Please answer the following questions to begin.</p>",
        "questions": [
            {
                "id": "name",
                "type": "text",
                "prompt_html": "What is your name?",
                "required": True,
            },
            {
                "id": "age",
                "type": "int",
                "prompt_html": "How old are you?",
                "required": True,
            },
        ],
        "next_key": "task_1",
    },

    "task_1": {
        "key": "task_1",
        "kind": "content",
        "text_html": "<h2>Task 1</h2><p>Observe the image and rate your agreement.</p>",
        "image_url": "https://via.placeholder.com/400x300",
        "questions": [
            {
                "id": "interest",
                "type": "likert",
                "prompt_html": "I found this task interesting.",
                "required": True,
                "options": [
                    {"value": 1, "label": "Strongly Disagree"},
                    {"value": 2, "label": "Disagree"},
                    {"value": 3, "label": "Neutral"},
                    {"value": 4, "label": "Agree"},
                    {"value": 5, "label": "Strongly Agree"},
                ],
            },
        ],
        "next_key": "done",
    },
    "done": {
        "key": "done",
        "kind": "content",
        "text_html": "<h2>Thank you!</h2><p>You have completed the study.</p>",
        "questions": [],
        "next_key": None,
    },
}


def get_first_screen_key():
    return "start"


def get_screen(key):
    return SCREENS.get(key)


def get_next_key(key):
    screen = get_screen(key)
    return screen["next_key"] if screen else None
