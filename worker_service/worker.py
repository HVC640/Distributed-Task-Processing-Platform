import uuid
from shared.redis.queue import fetch_task
from worker_service.task_executor import execute_task


def start_worker():
    WORKER_ID = str(uuid.uuid4())
    while True:
        print("Worker is waiting for tasks...")
        task_id = fetch_task()
        if task_id:
            print(f"Worker fetched task: {task_id}")
            execute_task(task_id, WORKER_ID)
