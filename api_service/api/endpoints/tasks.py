from fastapi import APIRouter, HTTPException
from shared.db import task_repository
from shared.models.task import CreateTaskRequest
from shared.redis import queue as redis_queue

# Create router
router = APIRouter()


@router.post("/tasks", response_model=dict)
async def create_task(request: CreateTaskRequest):
    """
    Create a new task
    """
    try:
        task_id = task_repository.add_task(
            task_type=request.task_type,
            payload=request.payload,
            priority=request.priority,
            uploaded_by=request.uploaded_by,
            scheduled_for=request.scheduled_for,
            max_retries=request.max_retries
        )
        redis_queue.enqueue_task(task_id, priority=request.priority)

        return {"task_id": task_id, "message": "Task created successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """
    Get a specific task by ID
    """
    try:
        task = task_repository.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve task: {str(e)}")


@router.get("/tasks")
async def get_tasks():
    """
    Get all tasks
    """
    try:
        tasks = task_repository.get_all_tasks()
        return tasks

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")


@router.put("/tasks/{task_id}/status")
async def update_task_status_endpoint(task_id: str, status: str, result: dict = None):
    """
    Update the status of a task
    """
    try:
        success = task_repository.update_task_status(task_id, status, result)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": "Task status updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update task status: {str(e)}")
