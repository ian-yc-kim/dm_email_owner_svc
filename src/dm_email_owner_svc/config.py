import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
SERVICE_PORT = os.getenv("SERVICE_PORT", 8000)

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

try:
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
except ValueError:
    OPENAI_TIMEOUT = 30

try:
    OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
except ValueError:
    OPENAI_MAX_RETRIES = 3
