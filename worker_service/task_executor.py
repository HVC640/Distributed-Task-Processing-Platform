from concurrent.futures import ThreadPoolExecutor, TimeoutError
from shared.redis.queue import add_to_processing_queue, remove_from_processing_queue
from shared.db.task_repository import get_task_by_id, claim_task, update_task_status, update_heartbeat
from shared.config.config import WORKER_CONFIG
from worker_service.handlers.registry import TASK_HANDLERS
import threading
import time


def is_still_owner(task_id, WORKER_ID):
    task = get_task_by_id(task_id)
    return task['worker_id'] == WORKER_ID


def heartbeat_loop(task_id, WORKER_ID, stop_event):
    while not stop_event.is_set():
        update_heartbeat(task_id, WORKER_ID)
        time.sleep(WORKER_CONFIG["heartbeat_interval"])


def execute_task(task_id, WORKER_ID):
    try:
        # Step 1: Claim task with lease
        if not claim_task(task_id, WORKER_ID):
            return

        task = get_task_by_id(task_id)
        handler = TASK_HANDLERS[task['task_type']]

        stop_heartbeat = threading.Event()

        # Step 2: Start heartbeat thread
        heartbeat_thread = threading.Thread(
            target=heartbeat_loop,
            args=(task_id, WORKER_ID, stop_heartbeat),
            daemon=True
        )
        heartbeat_thread.start()

        # Step 3: Add to processing queue
        key = f"{task_id}"
        add_to_processing_queue(key)

        # Step 4: Execute task
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(handler, task['payload'])

            try:
                result = future.result(timeout=WORKER_CONFIG["worker_timeout"])

                # Step 5: Check ownership before marking complete
                if not is_still_owner(task_id, WORKER_ID):
                    print(
                        f"Lost ownership of task {task_id}, skipping completion.")
                    return

                update_task_status(task_id, "COMPLETED", result)

            except TimeoutError:
                update_task_status(
                    task_id, "FAILED", f"Timeout after {WORKER_CONFIG['worker_timeout']} seconds")
                return

        # Step 6: Cleanup
        remove_from_processing_queue(key)

    except Exception as e:
        update_task_status(task_id, "FAILED", str(e))

    finally:
        stop_heartbeat.set()
