import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """Formatter that serializes log records as JSON."""

    def __init__(self, service_name):
        super().__init__(fmt="%(message)s")
        self.service_name = service_name

    def format(self, record):
        log = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "event": getattr(record, "event", ""),
            "message": record.getMessage(),
        }

        extra_data = getattr(record, "extra_data", None)
        if isinstance(extra_data, dict):
            log.update(extra_data)

        return json.dumps(log)


def get_logger(service_name):
    logger = logging.getLogger(service_name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter(service_name))

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
