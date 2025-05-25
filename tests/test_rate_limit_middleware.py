import time
from dm_email_owner_svc.core import rate_limit

# use a dummy time module to avoid patching the global time module

def test_rate_limit_under_limit_and_exceeded(monkeypatch, client):
    # Freeze time to simulate within the same window
    fixed_time = 1000.0
    # Create a dummy time module with only time() patched
    DummyTime = type("DummyTime", (), {"time": staticmethod(lambda: fixed_time)})
    monkeypatch.setattr(rate_limit, "time", DummyTime)
    # First 10 requests should succeed
    for _ in range(10):
        response = client.get("/ping")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() == {"ping": "pong"}
    # 11th request should be rate-limited
    response = client.get("/ping")
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    assert response.json() == {"detail": "Rate limit exceeded. Max 10 requests per minute."}


def test_rate_limit_window_rollover(monkeypatch, client):
    # Simulate time progression: 11 calls at base_time, then a rollover
    base_time = 1000.0
    times = [base_time] * 11 + [base_time + 61.0]
    def fake_time():
        # Return next simulated timestamp, fallback to rollover time if list is empty
        if times:
            return times.pop(0)
        return base_time + 61.0
    # Create dummy time module with fake_time as staticmethod
    FakeTime = type("FakeTime", (), {"time": staticmethod(fake_time)})
    monkeypatch.setattr(rate_limit, "time", FakeTime)
    # First 10 allowed
    for _ in range(10):
        resp = client.get("/ping")
        assert resp.status_code == 200
    # 11th denied
    resp = client.get("/ping")
    assert resp.status_code == 429
    # After window rollover, allowed again
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"ping": "pong"}
