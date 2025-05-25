import logging
import time
import sys
import pytest
from dm_email_owner_svc.core.logging import configure_logging


def test_configure_logging_sets_up_queue_handler():
    configure_logging()
    root_logger = logging.getLogger()
    handlers = root_logger.handlers
    # Only one handler should be attached and it should be a QueueHandler
    from logging.handlers import QueueHandler
    assert len(handlers) == 1
    assert isinstance(handlers[0], QueueHandler)
    assert root_logger.level == logging.INFO


def test_logging_output(capsys):
    configure_logging()
    # Log multiple messages rapidly
    for i in range(3):
        logging.info(f"Test message {i}")
    # Allow background listener to process messages
    time.sleep(0.1)
    captured = capsys.readouterr()
    # Verify that all messages appear in stdout
    for i in range(3):
        assert f"Test message {i}" in captured.out