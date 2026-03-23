from recovery_service.recovery import start_recovery
from shared.logging.logger import get_logger

if __name__ == "__main__":
    logger = get_logger("recovery_service")
    logger.info("Starting Recovery Service...")
    start_recovery()
    logger.info("Recovery Service stopped.")
