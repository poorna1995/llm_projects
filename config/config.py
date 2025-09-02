import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
PUSHOVER_USER     = os.getenv("PUSHOVER_USER")
PUSHOVER_API      = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL      = "https://api.pushover.net/1/messages.json"
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")

NAME = "poorna praneesha"