import os
# Set environment variable so that the app initializes a dummy OpenAI client in testing mode
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient


# This test verifies rate limit middleware behavior

def test_rate_limit_under_limit_and_exceeded(client):
    # Reset the rate limiter state by calling /ping with the special header
    reset_response = client.get("/ping", headers={"X-Test-Reset-RateLimit": "true"})
    # Ensure the reset call itself is successful
    assert reset_response.status_code == 200, "Reset endpoint did not return 200"
    
    # Send 10 requests without any special headers, these should be allowed
    success_count = 0
    for i in range(10):
        response = client.get("/ping")
        if response.status_code == 200:
            success_count += 1
    assert success_count == 10, f"Expected 10 successful responses, got {success_count}"
    
    # The 11th request should be rate limited
    response = client.get("/ping")
    assert response.status_code == 429, "Expected 429 response for rate limit exceeded"
