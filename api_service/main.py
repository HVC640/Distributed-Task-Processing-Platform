from fastapi import FastAPI
from api.endpoints.tasks import router as tasks_router

app = FastAPI(title="Distributed-Task-Processing-Platform")

app.include_router(tasks_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)