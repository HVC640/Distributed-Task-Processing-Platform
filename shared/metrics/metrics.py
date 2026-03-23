import time
import redis
import os
from shared.config.config import REDIS_CONFIG

# Assuming a Redis client is initialized; adjust as needed
r = redis.Redis(
    host=os.getenv('REDIS_HOST', REDIS_CONFIG["host"]),
    port=os.getenv('REDIS_PORT', REDIS_CONFIG["port"]),
    db=os.getenv('REDIS_DATABASE', REDIS_CONFIG["database"])
)

# -------- COUNTERS --------
def increment(metric_name: str, value: int = 1):
    r.incrby(f"metrics:{metric_name}", value)


def get_counter(metric_name: str):
    return int(r.get(f"metrics:{metric_name}") or 0)


# -------- TIMING --------
def record_execution_time(metric_name: str, duration: float):
    # store last 100 values only
    key = f"metrics:{metric_name}"
    r.lpush(key, duration)
    r.ltrim(key, 0, 99)


def get_avg_execution_time(metric_name: str):
    values = r.lrange(f"metrics:{metric_name}", 0, -1)
    if not values:
        return 0
    values = [float(v) for v in values]
    return sum(values) / len(values)


# -------- GAUGES --------
def set_value(metric_name: str, value: int):
    r.set(f"metrics:{metric_name}", value)


def get_value(metric_name: str):
    return int(r.get(f"metrics:{metric_name}") or 0)
