import traceback

from shared.config.config import WORKER_CONFIG
from shared.db import connections
import json


def add_task(task_type, payload, priority, uploaded_by, scheduled_for=None, max_retries=3):
    """
    Inserts a new task into the tasks table.
    """

    query = """
    INSERT INTO tasks (
        task_type,
        payload,
        priority,
        status,
        uploaded_by,
        scheduled_for,
        max_retries
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING task_id;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    task_type,
                    json.dumps(payload),
                    priority,
                    "PENDING",
                    uploaded_by,
                    scheduled_for,
                    max_retries
                )
            )

            task_id = cursor.fetchone()["task_id"]
            conn.commit()

            return task_id

    finally:
        conn.close()


def get_task_by_id(task_id):
    """
    Retrieves a task by its ID.
    """
    query = """
    SELECT task_id, task_type, priority, payload, status, uploaded_by,
           scheduled_for, lease_expires_at, worker_id, last_heartbeat, 
           retry_count, max_retries, created_at, started_at, result
    FROM tasks
    WHERE task_id = %s;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (task_id,))
            result = cursor.fetchone()

            if result:
                # Convert the result to match our Task model
                return {
                    "id": str(result["task_id"]),
                    "task_type": result["task_type"],
                    "priority": result["priority"],
                    "payload": result["payload"] if isinstance(result["payload"], dict) else json.loads(result["payload"] or "{}"),
                    "status": result["status"].lower(),
                    "uploaded_by": result["uploaded_by"],
                    "scheduled_for": result["scheduled_for"],
                    "lease_expires_at": result["lease_expires_at"],
                    "worker_id": result["worker_id"],
                    "last_heartbeat": result["last_heartbeat"],
                    "retry_count": result["retry_count"],
                    "max_retries": result["max_retries"],
                    "created_at": result["created_at"],
                    "started_at": result["started_at"],
                    "result": result["result"] if isinstance(result["result"], dict) else result["result"]
                }
            return None

    finally:
        conn.close()


def get_all_tasks():
    """
    Retrieves all tasks from the database.
    """
    query = """
    SELECT task_id, task_type, priority, payload, status, uploaded_by,
           scheduled_for, max_retries, created_at, started_at, result
    FROM tasks
    ORDER BY created_at DESC;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

            tasks = []
            for result in results:
                task = {
                    "id": str(result["task_id"]),
                    "task_type": result["task_type"],
                    "priority": result["priority"],
                    "status": result["status"].lower(),
                    "payload": result["payload"],
                    "created_at": result["created_at"],
                    "started_at": result["started_at"],
                    "result": result["result"]
                }
                tasks.append(task)

            return tasks
    except Exception as e:
        return []

    finally:
        conn.close()


def update_task_status(task_id, status, result=None):
    """
    Updates the status of a task and optionally sets the result.
    """
    query = """
    UPDATE tasks
    SET status = %s, result = %s
    WHERE task_id = %s;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    status.upper(),
                    json.dumps(result) if result else None,
                    task_id
                )
            )
            conn.commit()

            return cursor.rowcount > 0

    finally:
        conn.close()


def claim_task(task_id, worker_id):
    """
    Atomically claims a task for processing by updating its status.
    Returns True if the task was successfully claimed, False otherwise.
    """
    query = """
    UPDATE tasks
        SET
            status = 'RUNNING',
            worker_id = %s,
            last_heartbeat = now(),
            lease_expires_at = now() + interval '%s seconds'
        WHERE task_id = %s
        AND status = 'PENDING';
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query, (worker_id, WORKER_CONFIG["lease_duration"], task_id))
            conn.commit()

            return cursor.rowcount > 0

    finally:
        conn.close()


def update_task_retries(task_id, retries):
    """
    Updates the retry count of a task.
    """
    query = """
    UPDATE tasks
    SET retry_count = %s
    WHERE task_id = %s;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (retries, task_id))
            conn.commit()

            return cursor.rowcount > 0

    finally:
        conn.close()


def update_heartbeat(task_id, WORKER_ID):
    """
    Updates the heartbeat timestamp and lease expiration for a task.
    """
    query = """
    UPDATE tasks
    SET last_heartbeat = now(), lease_expires_at = now() + interval '%s seconds'
    WHERE task_id = %s AND worker_id = %s;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query, (WORKER_CONFIG["lease_duration"], task_id, WORKER_ID))
            conn.commit()

    finally:
        conn.close()


def clear_task_ownership(task_id):
    """
    Clears the worker ownership and lease information for a task.
    """
    query = """
    UPDATE tasks
    SET worker_id = NULL, last_heartbeat = NULL, lease_expires_at = NULL
    WHERE task_id = %s;
    """

    conn = connections.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (task_id,))
            conn.commit()

    finally:
        conn.close()
