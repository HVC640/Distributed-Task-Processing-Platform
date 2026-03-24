import traceback

from fastapi import Request
from fastapi import APIRouter, HTTPException
from shared.db import task_repository
from shared.models.task import CreateTaskRequest
from shared.redis import queue as redis_queue
from shared.rate_limiter import token_bucket
from shared.logging.logger import get_logger
from shared.metrics import metrics

logger = get_logger("api_service")

# Create router
router = APIRouter()


def get_user_id(request: Request, uploaded_by: str | None):

    def get_client_ip(request: Request):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "anonymous"

    # Priority 1: API Key
    api_key = request.headers.get("X-API-KEY")
    if api_key:
        return f"api_key:{api_key}"

    # Priority 2: Uploaded_by (optional)
    if uploaded_by:
        return f"user:{uploaded_by}"

    # Priority 3: IP fallback
    return f"ip:{get_client_ip(request)}"


@router.post("/tasks", response_model=dict)
async def create_task(http_request: Request, request: CreateTaskRequest):
    """
    Create a new task
    """
    try:
        user_id = get_user_id(http_request, request.uploaded_by)
        if not token_bucket.is_allowed(user_id):
            logger.warning(
                "Rate limit exceeded for user",
                extra={
                    "extra_data": {"event": "rate_limit_exceeded", "user_id": user_id}
                },
            )
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )

        logger.info(
            "Creating new task",
            extra={
                "extra_data": {
                    "event": "create_task",
                    "request": request.model_dump_json(),
                }
            },
        )
        task_id = task_repository.add_task(
            task_type=request.task_type,
            payload=request.payload,
            priority=request.priority,
            uploaded_by=request.uploaded_by,
            scheduled_for=request.scheduled_for,
            max_retries=request.max_retries,
        )
        redis_queue.enqueue_task(task_id, priority=request.priority)
        metrics.increment("tasks_created")
        logger.info(
            "Task created and enqueued",
            extra={"extra_data": {"event": "task_created", "task_id": task_id}},
        )

        return {"task_id": task_id, "message": "Task created successfully"}

    except Exception as e:
        logger.error(
            "Failed to create task",
            extra={
                "extra_data": {
                    "event": "create_task_failed",
                    "request": request.model_dump_json(),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            },
        )
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """
    Get a specific task by ID
    """
    try:
        logger.info(
            "Retrieving task",
            extra={"extra_data": {"event": "get_task", "task_id": task_id}},
        )
        task = task_repository.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    except Exception as e:
        logger.error(
            "Failed to retrieve task",
            extra={
                "extra_data": {
                    "event": "get_task_failed",
                    "task_id": task_id,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve task: {str(e)}"
        )


@router.get("/tasks")
async def get_tasks():
    """
    Get all tasks
    """
    try:
        logger.info(
            "Retrieving all tasks", extra={"extra_data": {"event": "get_tasks"}}
        )
        tasks = task_repository.get_all_tasks()
        return tasks

    except HTTPException:
        logger.warning(
            "No tasks found", extra={"extra_data": {"event": "get_tasks_no_tasks"}}
        )
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve tasks",
            extra={
                "extra_data": {
                    "event": "get_tasks_failed",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve tasks: {str(e)}"
        )


@router.put("/tasks/{task_id}/status")
async def update_task_status_endpoint(task_id: str, status: str, result: dict = None):
    """
    Update the status of a task
    """
    try:
        logger.info(
            "Updating task status",
            extra={
                "extra_data": {
                    "event": "update_task_status",
                    "task_id": task_id,
                    "status": status,
                    "result": result,
                }
            },
        )
        success = task_repository.update_task_status(task_id, status, result)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": "Task status updated successfully"}

    except HTTPException:
        logger.warning(
            "Task not found for status update",
            extra={
                "extra_data": {
                    "event": "update_task_status_not_found",
                    "task_id": task_id,
                }
            },
        )
        raise
    except Exception as e:
        logger.error(
            "Failed to update task status",
            extra={
                "extra_data": {
                    "event": "update_task_status_failed",
                    "task_id": task_id,
                    "status": status,
                    "result": result,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update task status: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics():
    """
    Get API metrics
    """
    return {
        "tasks_created": metrics.get_counter("tasks_created"),
        "task_completed": metrics.get_counter("tasks_completed"),
        "tasks_retried": metrics.get_counter("tasks_retried"),
        "tasks_timeoutd": metrics.get_counter("tasks_timeoutd"),
        "tasks_failed": metrics.get_counter("tasks_failed"),
        "task_execution_time": metrics.get_avg_execution_time("task_execution_time"),
    }
