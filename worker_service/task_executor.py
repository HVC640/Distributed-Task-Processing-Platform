from shared.redis.queue import add_to_processing_queue, remove_from_processing_queue
from shared.db.task_repository import get_task_by_id, claim_task, update_task_status
from worker_service.handlers.registry import TASK_HANDLERS
import os
import sys

# Simple dynamic import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)


def execute_task(task_id):
    task = get_task_by_id(task_id)

    handler = TASK_HANDLERS[task['task_type']]

    try:
        if claim_task(task_id, "RUNNING"):
            add_to_processing_queue(f"{task_id}:{task['started_at']}")
            result = handler(task['payload'])
            update_task_status(task_id, "COMPLETED", result)
            remove_from_processing_queue(f"{task_id}:{task['started_at']}")

    except Exception as e:
        update_task_status(task_id, "FAILED", str(e))
