import uvicorn
from fastapi import FastAPI
from api_service.api.endpoints.tasks import router as tasks_router
from shared.logging.logger import get_logger

app = FastAPI(title="Distributed-Task-Processing-Platform")

app.include_router(tasks_router)

if __name__ == "__main__":
    logger = get_logger("api_service")
    logger.info("Starting API service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    logger.info("API service stopped.")
