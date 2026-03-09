import importlib
import json
import os
import sys

# Simple dynamic import of Task model
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.db import connections


def add_task(task_type, payload, uploaded_by, scheduled_for=None, max_retries=3):
    """
    Inserts a new task into the tasks table.
    """

    query = """
    INSERT INTO tasks (
        task_type,
        payload,
        status,
        uploaded_by,
        scheduled_for,
        max_retries
    )
    VALUES (%s, %s, %s, %s, %s, %s)
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
    SELECT task_id, task_type, payload, status, uploaded_by,
           scheduled_for, max_retries, created_at, started_at, result
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
                    "status": result["status"].lower(),
                    "payload": result["payload"] if isinstance(result["payload"], dict) else json.loads(result["payload"] or "{}"),
                    "created_at": result["created_at"],
                    "started_at": result["started_at"],
                    "result": result["result"] if isinstance(result["result"], dict) else (json.loads(result["result"]) if result["result"] else None)
                }
            return None

    finally:
        conn.close()


def get_all_tasks():
    """
    Retrieves all tasks from the database.
    """
    query = """
    SELECT task_id, task_type, payload, status, uploaded_by,
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
                    "status": result["status"].lower(),
                    "payload": result["payload"] if isinstance(result["payload"], dict) else json.loads(result["payload"] or "{}"),
                    "created_at": result["created_at"],
                    "started_at": result["started_at"],
                    "result": result["result"] if isinstance(result["result"], dict) else (json.loads(result["result"]) if result["result"] else None)
                }
                tasks.append(task)

            return tasks

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
