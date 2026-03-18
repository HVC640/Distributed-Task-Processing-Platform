from shared.db.task_repository import get_task_by_id, update_task_status, update_task_retries
from shared.redis.queue import remove_processing_task, enqueue_task
from shared.config.config import RECOVERY_CONFIG
from datetime import datetime, timezone
import os
import sys

# Simple dynamic import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)


def should_recover(started_at, threshold=RECOVERY_CONFIG["task_timeout"]):
    started_dt = datetime.fromisoformat(started_at)
    now_dt = datetime.now(timezone.utc)

    elapsed = (now_dt - started_dt.astimezone(timezone.utc)).total_seconds()
    return elapsed >= threshold


def recover_task(key):
    task_id, started_at = key.split("||")
    if not should_recover(started_at):
        print(f"Task {key} still within processing window. Skipping.")
        return
    print(f"Recovering task: {key}")

    remove_processing_task(key)
    task = get_task_by_id(task_id)
    max_retries = task['max_retries']
    retry_count = task['retry_count']

    if max_retries <= retry_count:
        print(f"Task {task_id} has exceeded max retries. Marking as failed.")
        update_task_status(task_id, "FAILED", "Exceeded max retries")
        return

    print(f"Retrying task {task_id}. Attempt {retry_count + 1}")
    update_task_retries(task_id, retry_count + 1)
    update_task_status(task_id, "PENDING")

    priority = task['priority']
    enqueue_task(task_id, priority)
    print(f"Task {task_id} re-enqueued with priority {priority}")
