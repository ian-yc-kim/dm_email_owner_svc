from fastapi import Request


def get_openai_client(request: Request):
    """Dependency function to return the OpenAIClient instance from app state."""
    return request.app.state.openai_client
