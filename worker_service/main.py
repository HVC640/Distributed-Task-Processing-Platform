import os
import sys

# Simple dynamic import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from worker_service.worker import start_worker

if __name__ == "__main__":
    print("Starting Worker Service...")
    start_worker()
    print("Worker Service stopped.")
