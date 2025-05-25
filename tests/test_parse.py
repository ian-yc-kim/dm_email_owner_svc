import pytest
from fastapi import status


def test_parse_valid_request(client):
    payload = {"html_content": "<p>Hello</p>", "emails": ["test@example.com", "foo@bar.com"]}
    response = client.post("/parse", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


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
