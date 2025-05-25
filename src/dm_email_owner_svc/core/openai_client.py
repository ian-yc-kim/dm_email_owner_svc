import os
import logging
import openai

# Attempt to import exception classes from openai.error; if not available, fall back to Exception
try:
    from openai.error import APIError, Timeout, OpenAIError
except ImportError:
    APIError = Timeout = OpenAIError = Exception

from dm_email_owner_svc.config import OPENAI_API_KEY, OPENAI_MODEL_NAME, OPENAI_TIMEOUT, OPENAI_MAX_RETRIES


class OpenAIClient:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError('Missing OpenAI API key')
        try:
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            logging.error(e, exc_info=True)
            raise

    def chat_completion(self, messages: list[dict]) -> dict:
        try:
            client_with_options = self.client.with_options(max_retries=OPENAI_MAX_RETRIES, timeout=OPENAI_TIMEOUT)
            # Call the OpenAI chat completion endpoint
            result = client_with_options.beta.chat.completion.create(model=OPENAI_MODEL_NAME, messages=messages)
            return result
        except (APIError, Timeout, OpenAIError) as e:
            # Log error message without exposing sensitive API key
            logging.error('Error during chat_completion: OpenAI API error occurred', exc_info=True)
            # Returning a structured error response
            return {"error": "OpenAI API error"}
        except Exception as e:
            logging.error(e, exc_info=True)
            return {"error": "Unexpected error"}
