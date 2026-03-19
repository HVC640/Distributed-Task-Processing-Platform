from recovery_service.task_recovery import recover_task
from shared.redis.queue import fetch_processing_task
from shared.config.config import RECOVERY_CONFIG
import time

def start_recovery():
    while True:
        print("Checking for tasks to recover...")
        tasks = fetch_processing_task()
        for key in tasks:
            print(f"Recovering key: {key}")
            recover_task(key)
        time.sleep(RECOVERY_CONFIG["recovery_interval"])  # Sleep for a while before checking for tasks
