from shared.db.task_repository import (
    get_task_by_id,
    update_task_status,
    update_task_retries,
    clear_task_ownership,
)
from shared.redis.queue import remove_processing_task, enqueue_task
from shared.logging.logger import get_logger
from shared.metrics import metrics
from datetime import datetime, timezone

logger = get_logger("recovery_service")


def should_recover(lease_expires_at):
    if isinstance(lease_expires_at, str):
        lease_dt = datetime.fromisoformat(lease_expires_at)
    else:
        lease_dt = lease_expires_at  # already datetime

    now_dt = datetime.now(timezone.utc)

    return now_dt >= lease_dt


def recover_task(task_id):
    logger.info(
        f"Attempting to recover task", extra={"extra_data": {"task_id": task_id}}
    )
    task = get_task_by_id(task_id)

    if not should_recover(task["lease_expires_at"]):
        logger.info(
            f"Task is not ready for recovery",
            extra={"extra_data": {"task_id": task_id}},
        )
        return

    logger.info(
        f"Recovering task",
        extra={
            "extra_data": {
                "task_id": task_id,
                "lease_expires_at": task["lease_expires_at"],
            }
        },
    )

    remove_processing_task(task_id)

    max_retries = task["max_retries"]
    retry_count = task["retry_count"]

    if retry_count >= max_retries:
        logger.info(
            f"Task has exceeded max retries", extra={"extra_data": {"task_id": task_id}}
        )
        update_task_status(task_id, "FAILED", "Exceeded max retries")
        return

    update_task_retries(task_id, retry_count + 1)
    clear_task_ownership(task_id)
    update_task_status(task_id, "PENDING")

    enqueue_task(task_id, task["priority"])
    metrics.increment("tasks_retried")
    logger.info(
        f"Task re-enqueued for processing", extra={"extra_data": {"task_id": task_id}}
    )
