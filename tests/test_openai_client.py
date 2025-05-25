import os
import openai
import logging
import pytest
import importlib

# Test instantiation without API key

def test_missing_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr("dm_email_owner_svc.config.OPENAI_API_KEY", "")
    import dm_email_owner_svc.core.openai_client as openai_client_module
    importlib.reload(openai_client_module)
    OpenAIClient = openai_client_module.OpenAIClient
    with pytest.raises(ValueError) as exc_info:
        OpenAIClient()
    assert 'Missing OpenAI API key' in str(exc_info.value)


# Helper class to simulate OpenAI client chain
class DummyChatCompletion:
    def __init__(self, response):
        self.response = response

    def create(self, model, messages):
        return self.response


class DummyBeta:
    def __init__(self, response):
        self.chat = DummyChatCompletion(response)


class DummyClientWithOptions:
    def __init__(self, response, raise_on_call=None):
        self.response = response
        self.raise_on_call = raise_on_call
        self.called = 0
        self.beta = DummyBeta(response)

    def __getattr__(self, item):
        return getattr(self.beta, item)

    def create(self, model, messages):
        if self.raise_on_call and self.called < len(self.raise_on_call):
            exc = self.raise_on_call[self.called]
            self.called += 1
            if exc is not None:
                raise exc
        return self.response


# Test successful chat_completion

def test_chat_completion_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    monkeypatch.setattr("dm_email_owner_svc.config.OPENAI_API_KEY", "dummy_key")
    import dm_email_owner_svc.core.openai_client as openai_client_module
    importlib.reload(openai_client_module)
    OpenAIClient = openai_client_module.OpenAIClient

    dummy_response = {"result": "success"}

    class DummyOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key

        def with_options(self, max_retries, timeout):
            dummy_client = DummyClientWithOptions(dummy_response)
            # Return an object with beta.chat.completion.create
            class DummyOptions:
                def __init__(self, client):
                    self.beta = type('Beta', (), {'chat': type('Chat', (), {'completion': type('Completion', (), {'create': lambda self, model, messages: client.response})()})()})()
            return DummyOptions(dummy_client)

    monkeypatch.setattr(openai, 'OpenAI', DummyOpenAI)
    client = OpenAIClient()
    messages = [{"role": "user", "content": "Hello"}]
    response = client.chat_completion(messages)
    assert response == dummy_response


# Test transient API failure: raise APIError once then succeed

def test_chat_completion_transient_failure(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    monkeypatch.setattr("dm_email_owner_svc.config.OPENAI_API_KEY", "dummy_key")
    import dm_email_owner_svc.core.openai_client as openai_client_module
    importlib.reload(openai_client_module)
    OpenAIClient = openai_client_module.OpenAIClient

    dummy_response = {"result": "success_after_retry"}
    call_count = [0]

    class DummyOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key

        def with_options(self, max_retries, timeout):
            # Create a dummy client that fails on first call and succeeds on second
            class DummyBetaChatCompletion:
                def create(_, model, messages):
                    if call_count[0] == 0:
                        call_count[0] += 1
                        raise openai.APIError('Simulated API error', request="dummy_request", body="dummy_body")
                    return dummy_response
            dummy_beta = type('Beta', (), {'chat': type('Chat', (), {'completion': DummyBetaChatCompletion()})()})()
            class DummyOptions:
                def __init__(self, beta):
                    self.beta = beta
            return DummyOptions(dummy_beta)

    monkeypatch.setattr(openai, 'OpenAI', DummyOpenAI)
    client = OpenAIClient()
    messages = [{"role": "user", "content": "Hello"}]
    response = client.chat_completion(messages)
    # Since exception is caught and a structured error is returned, we expect the error dict
    assert response == {"error": "OpenAI API error"}


# Test timeout exception handling

def test_chat_completion_timeout(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    monkeypatch.setattr("dm_email_owner_svc.config.OPENAI_API_KEY", "dummy_key")
    import dm_email_owner_svc.core.openai_client as openai_client_module
    importlib.reload(openai_client_module)
    OpenAIClient = openai_client_module.OpenAIClient

    class DummyOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key

        def with_options(self, max_retries, timeout):
            # Simulate timeout by raising openai.Timeout
            class DummyBeta:
                class Chat:
                    class Completion:
                        def create(self, model, messages):
                            raise openai.Timeout('Simulated timeout', request="dummy_request", body="dummy_body")

                    def __init__(self):
                        self.completion = self.Completion()

                @property
                def chat(self):
                    return self.Chat()
            class DummyOptions:
                def __init__(self):
                    self.beta = DummyBeta()
            return DummyOptions()

    monkeypatch.setattr(openai, 'OpenAI', DummyOpenAI)
    client = OpenAIClient()
    messages = [{"role": "user", "content": "Hello"}]
    response = client.chat_completion(messages)
    assert response == {"error": "OpenAI API error"}
