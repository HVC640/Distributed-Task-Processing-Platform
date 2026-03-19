import os
import sys
import uuid

# Simple dynamic import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

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