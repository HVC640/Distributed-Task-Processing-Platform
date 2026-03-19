from shared.db.task_repository import get_task_by_id, update_task_status, update_task_retries, clear_task_ownership
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


def should_recover(lease_expires_at):
    lease_dt = datetime.fromisoformat(lease_expires_at)
    now_dt = datetime.now(timezone.utc)

    return now_dt >= lease_dt


def recover_task(task_id):
    task = get_task_by_id(task_id)

    if not should_recover(task['lease_expires_at']):
        return

    print(f"Recovering task: {task_id}")
    
    remove_processing_task(task_id)

    max_retries = task['max_retries']
    retry_count = task['retry_count']

    if retry_count >= max_retries:
        update_task_status(task_id, "FAILED", "Exceeded max retries")
        return

    update_task_retries(task_id, retry_count + 1)    
    clear_task_ownership(task_id)
    update_task_status(task_id, "PENDING")
    
    enqueue_task(task_id, task['priority'])
    print(f"Task {task_id} re-enqueued for processing.")
