import pytest
from fastapi import status

from dm_email_owner_svc.dependencies.openai_dependency import get_openai_client


class FakeOpenAIClient:
    def chat_completion(self, messages):
        # Return a synthetic valid response for testing
        return {
            "choices": [
                {"message": {"content": '[{"email": "test@example.com", "owner": "Owner A"}, {"email": "foo@bar.com", "owner": "Owner B"}]'} }
            ]
        }

class FakeErrorClient:
    def chat_completion(self, messages):
        return {"error": "OpenAI API error"}


def test_parse_valid_request(client):
    # Override the dependency to use a fake OpenAI client with a valid response
    client.app.dependency_overrides[get_openai_client] = lambda: FakeOpenAIClient()
    payload = {"html_content": "<p>Hello</p>", "emails": ["test@example.com", "foo@bar.com"]}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_200_OK
    expected = [
        {"email": "test@example.com", "owner": "Owner A"},
        {"email": "foo@bar.com", "owner": "Owner B"}
    ]
    assert response.json() == expected
    client.app.dependency_overrides = {}


def test_parse_downstream_error(client):
    # Override the dependency to simulate a downstream API error
    client.app.dependency_overrides[get_openai_client] = lambda: FakeErrorClient()
    payload = {"html_content": "<p>Hello</p>", "emails": ["test@example.com"]}
    response = client.post("/parse", json=payload)
    assert response.status_code == 502
    client.app.dependency_overrides = {}


def test_parse_invalid_empty_html(client):
    payload = {"html_content": "", "emails": ["test@example.com"]}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_parse_invalid_long_html(client):
    html = "a" * 50001
    payload = {"html_content": html, "emails": ["test@example.com"]}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_parse_invalid_few_emails(client):
    payload = {"html_content": "<html></html>", "emails": []}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_parse_invalid_many_emails(client):
    emails = [f"user{i}@example.com" for i in range(51)]
    payload = {"html_content": "<html></html>", "emails": emails}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_parse_invalid_email_format(client):
    payload = {"html_content": "<p>Hi</p>", "emails": ["not-an-email"]}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
