from shared.config.config import REDIS_CONFIG
import os
import sys
import redis

# Simple dynamic import of Task model
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Assuming a Redis client is initialized; adjust as needed
r = redis.Redis(
    host=REDIS_CONFIG["host"],
    port=REDIS_CONFIG["port"],
    db=REDIS_CONFIG["database"]
)


def enqueue_task(task_id, priority='low'):
    """
    Adds a task to the appropriate priority queue.
    """
    if priority == 'high':
        queue = 'high_priority_queue'
    elif priority == 'medium':
        queue = 'medium_priority_queue'
    else:
        queue = 'low_priority_queue'
    r.lpush(queue, task_id)


def dequeue_task():
    """
    Removes and returns a task from the highest priority queue that has items.
    Returns None if all queues are empty.
    """
    for queue in ['high_priority_queue', 'medium_priority_queue', 'low_priority_queue']:
        task = r.rpop(queue)
        if task:
            return task.decode('utf-8')  # Assuming task_id is a string
    return None


def add_to_processing_queue(task_id):
    """
    Adds a task to the processing queue.
    """
    r.lpush('processing_queue', task_id)


def remove_from_processing_queue():
    """
    Removes and returns a task from the processing queue.
    Returns None if the queue is empty.
    """
    task = r.rpop('processing_queue')
    if task:
        return task.decode('utf-8')
    return None
