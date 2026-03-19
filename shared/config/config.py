DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "admin"
}

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "database": 0
}

WORKER_CONFIG = {
    "num_workers": 1,
    "worker_timeout": 5,  # seconds
    "lease_duration": 30,  # seconds
    "heartbeat_interval": 10  # seconds
}

RECOVERY_CONFIG = {
    "recovery_interval": 10,  # seconds
    "task_timeout": 5  # seconds
}
