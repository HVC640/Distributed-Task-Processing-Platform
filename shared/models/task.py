from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Task(BaseModel):
    id: str
    status: str  # e.g., "PENDING", "RUNNING", "COMPLETED", "FAILED"
    payload: dict
    created_at: datetime
    result: Optional[dict] = None

# Request model for creating tasks
class CreateTaskRequest(BaseModel):
    task_type: str
    payload: Optional[dict] = None
    priority: Optional[str] = "low"
    uploaded_by: Optional[str] = "localhost"
    scheduled_for: str = None
    max_retries: int = 3
