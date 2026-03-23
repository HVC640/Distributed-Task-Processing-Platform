# Distributed Task Processing Platform — System Design

---

# 1. Goal

Build a **production-style distributed background job processing system** capable of:

* Accepting tasks via API
* Executing tasks asynchronously
* Handling worker crashes and partial failures
* Supporting retries and priority queues
* Scaling workers horizontally
* Preventing duplicate execution using lease-based ownership
* Providing observability (logging + metrics)
* Protecting APIs using rate limiting

Inspired by:

* Celery
* Sidekiq
* AWS SQS worker pipelines

---

# 2. High-Level Architecture

```text
Client
   │
   ▼
FastAPI API Service
   │
   ▼
PostgreSQL (Task Metadata + Ownership)
   │
   ▼
Redis (Priority Queues + Metrics + Rate Limiting)
   │
   ▼
Workers (BRPOP blocking + Lease + Heartbeat)
   │
   ▼
Task Execution
   │
   ▼
Update DB Status
```

Recovery Service ensures correctness using **lease expiration**.

---

# 3. System Components

## 3.1 API Service

Responsibilities:

* Task creation
* Payload validation (Pydantic)
* Rate limiting (Token Bucket via Redis)
* Metrics collection
* Exposing system metrics

Endpoints:

```text
POST /tasks
GET /tasks/{task_id}
GET /tasks
GET /metrics
```

---

## 3.2 Worker Service

Workers process tasks asynchronously.

### Worker Flow

```text
1. BRPOP from priority queues
2. Claim task using lease (DB)
3. Start heartbeat thread
4. Execute handler
5. Validate ownership before completion
6. Update DB status
7. Stop heartbeat
```

---

### Lease-Based Ownership

Worker claims task:

```sql
UPDATE tasks
SET
  status = 'RUNNING',
  worker_id = ?,
  lease_expires_at = now() + interval '30 seconds'
WHERE task_id = ?
AND status = 'PENDING'
```

---

### Heartbeat Mechanism

Worker periodically updates:

```text
last_heartbeat
lease_expires_at
```

---

### Ownership Validation

Before completing:

```text
Check worker_id == current worker
```

Prevents stale workers from corrupting state.

---

## 3.3 Recovery Service

Responsible for detecting and recovering **orphaned tasks**.

---

### Recovery Logic (Updated)

```sql
SELECT *
FROM tasks
WHERE status = 'RUNNING'
AND lease_expires_at < now()
```

---

### Recovery Flow

```text
Lease expired → worker assumed dead
↓
Clear ownership
↓
Increment retry_count
↓
Requeue task
```

---

# 4. Queue Architecture

Redis priority queues:

```text
high_priority_queue
medium_priority_queue
low_priority_queue
```

Workers consume using:

```text
BRPOP(high, medium, low)
```

---

# 5. Worker Model

* Fixed worker model (initial)
* Horizontal scaling supported

```text
docker-compose up --scale worker=5
```

Each worker processes one task at a time.

---

# 6. Task Lifecycle

```text
pending
   ↓
running (lease acquired)
   ↓
completed
   OR
failed
```

---

### Recovery Path

```text
running + lease expired
   ↓
retrying
   ↓
pending
```

---

# 7. Database Design

Primary table: `tasks`

```text
task_id (UUID PRIMARY KEY)
task_type
payload (JSONB)
status
uploaded_by
created_at
scheduled_for
started_at
completed_at
retry_count
max_retries
result (JSONB)
error_message
worker_id
last_heartbeat
lease_expires_at
```

---

# 8. Observability

## 8.1 Logging (Structured)

* JSON structured logs
* Centralized via Docker stdout
* Includes:

```text
timestamp
service
level
event
task_id
worker_id
message
```

---

## 8.2 Metrics

Stored in Redis.

Tracked metrics:

```text
tasks_created
tasks_completed
tasks_failed
tasks_retried
task_execution_time
tasks_in_queue
```

---

## 8.3 Metrics Endpoint

```text
GET /metrics
```

---

# 9. Rate Limiting

Token Bucket algorithm using Redis.

---

### Features

* Burst handling
* Distributed safe (Lua script)
* Per-user rate limiting

---

### Flow

```text
Request → Redis token bucket → allow / reject
```

---

# 10. Reliability Mechanisms (Updated)

| Mechanism        | Purpose                   |
| ---------------- | ------------------------- |
| DB Claim         | Prevent duplicate workers |
| Processing Queue | Prevent task loss         |
| Lease            | Ownership control         |
| Heartbeat        | Liveness detection        |
| Recovery Service | Fault recovery            |
| Timeout          | Long task protection      |

---

# 11. Repository Structure

```text
task-platform/

api_service/
worker_service/
recovery_service/

shared/
  db/
  models/
  logging/
  metrics/
  rate_limiter/

docker/
docker-compose.yml

system-design.md
architecture-diagram.md
engineering-decisions.md
```

---

# 12. Deployment Model

Docker Compose runs:

```text
API Service
Worker Service
Recovery Service
Redis
PostgreSQL
```

---

# 13. System Guarantees

| Property                           | Status |
| ---------------------------------- | ------ |
| At-least-once execution            | ✅      |
| Fault tolerance                    | ✅      |
| Horizontal scaling                 | ✅      |
| Duplicate prevention (best-effort) | ✅      |
| Exactly-once execution             | ❌      |

---

# 14. Key Design Tradeoffs

* Chose lease over strict locking → simpler distributed model
* Accepted at-least-once execution → practical reliability
* Used Redis for metrics → fast but non-persistent
* Used stdout logging → simple and scalable

---

# 15. Future Enhancements

* Prometheus + Grafana (metrics)
* ELK stack (logging)
* Kafka (event-driven system)
* Auto-scaling workers
* Task scheduling (cron-based)
* Multi-region support

---

# 16. Learning Outcomes

This system demonstrates:

* distributed system design
* lease-based ownership model
* fault tolerance & recovery
* async processing architecture
* observability (logs + metrics)
* API protection (rate limiting)
* production-style service design

---
