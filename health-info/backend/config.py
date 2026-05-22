import os
from dotenv import load_dotenv

# Use absolute path so uvicorn's reloader subprocess finds .env regardless of CWD
_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=_env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_WHATSAPP = os.getenv("USER_WHATSAPP", "")

GROQ_MODEL = "llama-3.1-8b-instant"
DB_PATH = os.path.join(os.path.dirname(__file__), "health.db")

DEFAULT_CALORIE_GOAL = 2000
DEFAULT_PROTEIN_GOAL = 150
DEFAULT_CARBS_GOAL = 250
DEFAULT_FAT_GOAL = 65

CALORIE_WARN_THRESHOLD = 0.90
CALORIE_EXCEED_THRESHOLD = 1.0
