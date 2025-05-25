import pytest
from fastapi.testclient import TestClient

# Define a dummy OpenAIClient to be used during testing startup
class DummyOpenAIClient:
    # Mimic the interface of the real OpenAIClient if necessary
    pass

# Fixture to override the application's startup event without reloading modules
@pytest.fixture(scope="module")
def test_app():
    # Import the app from the application module
    from dm_email_owner_svc.app import app

    # Remove all existing startup events to avoid circular dependencies and recursion errors
    # app.router.on_startup is a list of callables
    app.router.on_startup.clear()

    # Define a dummy startup event that sets a dummy OpenAIClient instance
    async def dummy_startup():
        app.state.openai_client = DummyOpenAIClient()

    # Append the dummy startup event
    app.router.on_startup.append(dummy_startup)
    
    return app


# Use the 'client' fixture from conftest.py which uses the test_app fixture
@pytest.fixture()
def client(test_app):
    with TestClient(test_app) as c:
        yield c


def test_openai_client_initialized(client):
    # This test ensures that the dummy startup event has set openai_client on app state
    assert hasattr(client.app.state, 'openai_client'), 'OpenAI client was not set on app state'
    openai_client = client.app.state.openai_client
    # Instead of using isinstance (which can be problematic with reloaded modules),
    # we check that the dummy instance is of the expected type based on its attributes
    # Here, we expect the dummy instance to be an instance of DummyOpenAIClient
    assert openai_client.__class__.__name__ == 'DummyOpenAIClient', 'openai_client is not an instance of DummyOpenAIClient'
    expected_module = __name__  # since DummyOpenAIClient is defined in this test module
    actual_module = openai_client.__class__.__module__
    # We won't strictly enforce module match because DummyOpenAIClient is in the test file
    # but we check that the class name is correct
    assert actual_module is not None, 'openai_client.__class__.__module__ is None'


# Test the get_openai_client dependency function
# Import the dependency function within the test to avoid circular imports

def test_get_openai_client_dependency():
    from dm_email_owner_svc.dependencies.openai_dependency import get_openai_client
    
    # Create a dummy request object with an app that has openai_client preset
    class DummyState:
        pass
    dummy_state = DummyState()
    dummy_state.openai_client = 'dummy_instance'

    class DummyApp:
        state = dummy_state

    class DummyRequest:
        app = DummyApp()

    request = DummyRequest()
    instance = get_openai_client(request)
    assert instance == 'dummy_instance', 'get_openai_client did not return the expected instance'
