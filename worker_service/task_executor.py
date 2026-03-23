from concurrent.futures import ThreadPoolExecutor, TimeoutError
from shared.redis.queue import add_to_processing_queue, remove_from_processing_queue
from shared.db.task_repository import get_task_by_id, claim_task, update_task_status, update_heartbeat
from shared.logging.logger import get_logger
from shared.metrics import metrics
from shared.config.config import WORKER_CONFIG
from worker_service.handlers.registry import TASK_HANDLERS
import threading
import time

logger = get_logger("worker_service")

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
            logger.warning("Failed to claim task, it may have been claimed by another worker", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
            return

        start_time = time.time()

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
        logger.info("Heartbeat thread started", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})

        # Step 3: Add to processing queue        
        key = f"{task_id}"
        add_to_processing_queue(key)
        logger.info("Task added to processing queue", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})

        # Step 4: Execute task
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(handler, task['payload'])

            try:
                result = future.result(timeout=WORKER_CONFIG["worker_timeout"])

                # Step 5: Check ownership before marking complete
                if not is_still_owner(task_id, WORKER_ID):
                    logger.warning("Lost ownership of task, skipping completion", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
                    return

                update_task_status(task_id, "COMPLETED", result)

            except TimeoutError:
                logger.error("Task timed out", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
                update_task_status(
                    task_id, "FAILED", f"Timeout after {WORKER_CONFIG['worker_timeout']} seconds")
                metrics.increment("tasks_timeoutd")
                return

        # Step 6: Cleanup
        remove_from_processing_queue(key)
        logger.info("Task removed from processing queue", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
        end_time = time.time()
        metrics.record_execution_time("task_execution_time", end_time - start_time)
        metrics.increment("tasks_completed")

    except Exception as e:
        logger.error("Unexpected error occurred", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
        update_task_status(task_id, "FAILED", str(e))
        metrics.increment("tasks_failed")

    finally:
        stop_heartbeat.set()
        logger.info("Heartbeat thread stopped", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
