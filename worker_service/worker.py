import uuid
from shared.redis.queue import fetch_task
from worker_service.task_executor import execute_task
from shared.logging.logger import get_logger

def start_worker():    
    WORKER_ID = str(uuid.uuid4())
    logger = get_logger("worker_service")

    while True:
        logger.info("Worker initialized", extra={"extra_data": {"worker_id": WORKER_ID}})
        task_id = fetch_task()
        if task_id:
            logger.info("Worker fetched task", extra={"extra_data": {"worker_id": WORKER_ID, "task_id": task_id}})
            execute_task(task_id, WORKER_ID)
