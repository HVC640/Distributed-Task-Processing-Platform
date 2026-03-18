import os
import sys

# Simple dynamic import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from recovery_service.recovery import start_recovery

if __name__ == "__main__":
    print("Starting Recovery Service...")
    start_recovery()
    print("Recovery Service stopped.")
