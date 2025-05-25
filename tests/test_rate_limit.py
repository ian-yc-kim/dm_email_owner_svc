import pytest
import time
from dm_email_owner_svc.core import RateLimiter

def test_under_limit(monkeypatch):
    # Simulate constant time
    fixed_time = 1000.0
    monkeypatch.setattr(time, "time", lambda: fixed_time)
    rl = RateLimiter(limit=10, window_size=60.0)
    for _ in range(10):
        assert rl.is_allowed("client1") is True
    # 11th request should be denied
    assert rl.is_allowed("client1") is False

def test_window_rollover(monkeypatch):
    # Simulate time progression
    base_time = 1000.0
    # 11 calls at base_time, then a rollover timestamp
    times = [base_time] * 11 + [base_time + 61.0]
    def fake_time():
        return times.pop(0)
    monkeypatch.setattr(time, "time", fake_time)
    rl = RateLimiter(limit=10, window_size=60.0)
    # 10 allowed in initial window
    for _ in range(10):
        assert rl.is_allowed("client1") is True
    # 11th in same window denied
    assert rl.is_allowed("client1") is False
    # Next after window rollover allowed
    assert rl.is_allowed("client1") is True

def test_multiple_clients(monkeypatch):
    # Simulate constant time
    fixed_time = 2000.0
    monkeypatch.setattr(time, "time", lambda: fixed_time)
    rl = RateLimiter(limit=1, window_size=60.0)
    # Client A allowed then denied
    assert rl.is_allowed("A") is True
    assert rl.is_allowed("A") is False
    # Client B independent
    assert rl.is_allowed("B") is True
