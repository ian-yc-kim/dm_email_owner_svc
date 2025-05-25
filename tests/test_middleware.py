import json
import logging

def test_log_middleware_success(client, caplog):
    caplog.set_level(logging.INFO)
    # Test GET /ping
    response = client.get("/ping")
    assert response.status_code == 200
    logs = [record.getMessage() for record in caplog.records]
    found = any(
        msg.startswith("GET /ping") and "payload_size=0 bytes" in msg and
        "status_code=200" in msg and "duration_ms=" in msg
        for msg in logs
    )
    assert found, f"Expected log for GET /ping not found. Logs: {logs}"
    caplog.clear()
    # Test POST /echo
    payload = {"key": "value"}
    # Match httpx JSON encoding without spaces
    body = json.dumps(payload, separators=(',', ':')).encode()
    response = client.post("/echo", json=payload)
    assert response.status_code == 200
    logs = [record.getMessage() for record in caplog.records]
    expected_size = len(body)
    found = any(
        msg.startswith("POST /echo") and f"payload_size={expected_size} bytes" in msg and
        "status_code=200" in msg
        for msg in logs
    )
    assert found, f"Expected log for POST /echo not found. Logs: {logs}"


def test_log_middleware_exception(client, caplog):
    caplog.set_level(logging.ERROR)
    response = client.get("/error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert any("Unhandled exception during request" in record.getMessage() for record in error_logs), \
        f"Expected error log for exception not found. Logs: {[r.getMessage() for r in caplog.records]}"