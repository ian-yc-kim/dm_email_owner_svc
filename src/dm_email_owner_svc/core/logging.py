import logging
import queue
import sys
from logging.handlers import QueueHandler, QueueListener

def configure_logging() -> None:
    """
    Configure root logger to use non-blocking QueueHandler and background QueueListener.
    """
    try:
        # Create a thread-safe queue for log records
        log_queue: queue.Queue[logging.LogRecord] = queue.Queue()

        # Set up the queue handler at INFO level
        queue_handler = QueueHandler(log_queue)
        queue_handler.setLevel(logging.INFO)

        # Set up a standard output handler with formatter
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        output_handler = logging.StreamHandler(sys.stdout)
        output_handler.setFormatter(formatter)
        output_handler.setLevel(logging.INFO)

        # Start the listener in a separate thread
        listener = QueueListener(log_queue, output_handler)
        listener.start()

        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(logging.INFO)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise
