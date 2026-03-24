DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "task_db",
    "user": "postgres",
    "password": "admin",
}

REDIS_CONFIG = {"host": "localhost", "port": 6379, "database": 0}

RATE_LIMIT_CONFIG = {"capacity": 10, "refill_rate": 1}  # max burst  # tokens per second

WORKER_CONFIG = {
    "num_workers": 1,
    "worker_timeout": 60,  # seconds
    "lease_duration": 30,  # seconds
    "heartbeat_interval": 10,  # seconds
}

RECOVERY_CONFIG = {"recovery_interval": 10, "task_timeout": 5}  # seconds  # seconds
