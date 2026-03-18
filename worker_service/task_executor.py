from concurrent.futures import ThreadPoolExecutor, TimeoutError
from shared.redis.queue import add_to_processing_queue, remove_from_processing_queue
from shared.db.task_repository import get_task_by_id, claim_task, update_task_status
from shared.config.config import WORKER_CONFIG
from worker_service.handlers.registry import TASK_HANDLERS
import os
import sys

# Simple dynamic import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)


def execute_task(task_id):
    try:
        if claim_task(task_id, "RUNNING"):
            task = get_task_by_id(task_id)
            handler = TASK_HANDLERS[task['task_type']]
            key = f"{task_id}||{task['started_at']}"
            add_to_processing_queue(key)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(handler, task['payload'])

                try:
                    result = future.result(timeout=WORKER_CONFIG["worker_timeout"])  # ⏱ timeout here
                    update_task_status(task_id, "COMPLETED", result)

                except TimeoutError:
                    update_task_status(task_id, "FAILED", f"Timeout after {WORKER_CONFIG['worker_timeout']}s")
                    return

            remove_from_processing_queue(key)

    except Exception as e:
        update_task_status(task_id, "FAILED", str(e))
