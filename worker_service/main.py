from worker_service.worker import start_worker
from shared.logging.logger import get_logger

if __name__ == "__main__":
    logger = get_logger("worker_service")
    logger.info("Starting Worker Service...")
    start_worker()
    logger.info("Worker Service stopped.")
