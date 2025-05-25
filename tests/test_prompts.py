import pytest

from dm_email_owner_svc.core.prompts import build_email_owner_prompt


def test_build_email_owner_prompt():
    # Sample HTML content and emails
    html_content = "<html><body><p>Contact: john.doe@example.com - John Doe, jane.smith@example.com is not available</p></body></html>"
    emails = ["john.doe@example.com", "jane.smith@example.com"]
    
    # Build the prompt messages
    messages = build_email_owner_prompt(html_content, emails)
    
    # Assert that the returned structure is a list of two dictionaries
    assert isinstance(messages, list), "Output should be a list"
    assert len(messages) == 2, "There should be exactly two message dictionaries"
    
    # Verify the system message
    system_message = messages[0]
    assert system_message.get("role") == "system", "First message should have role 'system'"
    system_content = system_message.get("content", "")
    assert isinstance(system_content, str) and len(system_content) > 0, "System content should be a non-empty string"
    
    # Verify the user message
    user_message = messages[1]
    assert user_message.get("role") == "user", "Second message should have role 'user'"
    user_content = user_message.get("content", "")
    assert isinstance(user_content, str) and len(user_content) > 0, "User content should be a non-empty string"
    
    # Check that the user prompt includes the provided HTML content and emails
    assert html_content in user_content, "HTML content should be included in the user prompt"
    for email in emails:
        assert email in user_content, f"Email {email} should be included in the user prompt"
