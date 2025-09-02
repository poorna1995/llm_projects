import os
from dotenv import load_dotenv

load_dotenv(override=True)

PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_API = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

NAME = "poorna praneesha"
