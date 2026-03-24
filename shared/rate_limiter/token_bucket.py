import os
import time
import redis
from shared.config.config import REDIS_CONFIG, RATE_LIMIT_CONFIG

# Assuming a Redis client is initialized; adjust as needed
r = redis.Redis(
    host=os.getenv("REDIS_HOST", REDIS_CONFIG["host"]),
    port=os.getenv("REDIS_PORT", REDIS_CONFIG["port"]),
    db=os.getenv("REDIS_DATABASE", REDIS_CONFIG["database"]),
)

RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local data = redis.call("HMGET", key, "tokens", "last_refill")

local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_refill = now
end

local elapsed = now - last_refill
tokens = math.min(capacity, tokens + elapsed * refill_rate)

if tokens < 1 then
    redis.call("HMSET", key, "tokens", tokens, "last_refill", now)
    return 0
end

tokens = tokens - 1

redis.call("HMSET", key, "tokens", tokens, "last_refill", now)

return 1
"""


def is_allowed(user_id: str):
    key = f"rate_limit:{user_id}"

    allowed = r.eval(
        RATE_LIMIT_SCRIPT,
        1,
        key,
        RATE_LIMIT_CONFIG["capacity"],
        RATE_LIMIT_CONFIG["refill_rate"],
        time.time(),
    )

    return bool(allowed)
