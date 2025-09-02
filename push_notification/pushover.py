import requests
from config import PUSHOVER_USER, PUSHOVER_API, PUSHOVER_URL


def validate_pushover():
    if PUSHOVER_USER:
        print(f'Pushover user found and starts with {PUSHOVER_USER[:4]}')
    else:
        print("Pushover user not found")

    if PUSHOVER_API:
        print(f'Pushover API found and starts with {PUSHOVER_API[:4]}')
    else:
        print("Pushover API not found")


def push(text: str, title="Pushover Notification"):
    """Send a notification using Pushover"""
    if not (PUSHOVER_USER and PUSHOVER_API):
        print("Pushover not configured")
        return

    payload = {
        "token": PUSHOVER_API,
        "user": PUSHOVER_USER,
        "message": text,
        "title": title
    }
    requests.post(PUSHOVER_URL, data=payload)
