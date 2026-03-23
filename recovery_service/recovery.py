from recovery_service.task_recovery import recover_task
from shared.redis.queue import fetch_processing_task
from shared.config.config import RECOVERY_CONFIG
from shared.logging.logger import get_logger
import time

def start_recovery():
    logger = get_logger("recovery_service")
    while True:
        logger.info("Checking for tasks to recover...")
        tasks = fetch_processing_task()
        for key in tasks:
            logger.info(f"Recovering task with key: {key}")
            recover_task(key)
        time.sleep(RECOVERY_CONFIG["recovery_interval"])  # Sleep for a while before checking for tasks
