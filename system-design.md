# Distributed Task Processing Platform — System Design

## 1. Goal

Build a distributed background job processing system capable of:

* Accepting tasks via API
* Executing tasks asynchronously
* Handling worker crashes
* Supporting retries and priority queues
* Scaling workers horizontally
* Recovering stuck tasks automatically

This system is inspired by job systems like:

* Celery
* Sidekiq
* AWS SQS worker pipelines

---

# 2. High-Level Architecture

```
Client
   │
   ▼
FastAPI API Service
   │
   ▼
PostgreSQL (Task Metadata)
   │
   ▼
Redis Main Queue
   │
   ▼
Workers (BRPOP blocking)
   │
   ▼
Processing Queue
   │
   ▼
Task Execution
   │
   ▼
Update DB Status
   │
   ▼
Remove from Processing Queue
```

Recovery Service periodically checks for stuck tasks and requeues them.

---

# 3. System Components

## 3.1 API Service

Responsible for:

* Creating tasks
* Validating task payload
* Pushing task IDs to Redis queue
* Providing task status APIs

Endpoints:

```
POST /tasks
GET /tasks/{task_id}
GET /tasks
```

---

## 3.2 Worker Service

Workers run continuously and process tasks.

Worker flow:

```
1. BRPOP main_queue
2. Move task_id → processing_queue
3. Claim task in DB (pending → running)
4. Execute handler(task.payload)
5. Update DB status
6. Remove task from processing_queue
```

Workers execute Python handler functions mapped by `task_type`.

Example:

```
TASK_HANDLERS = {
  "send_email": send_email_handler,
  "resize_image": resize_image_handler
}
```

---

## 3.3 Recovery Service

Background process responsible for detecting stuck tasks.

Runs periodically (e.g. every 2 minutes).

Logic:

```
SELECT *
FROM tasks
WHERE status = 'running'
AND started_at < now() - timeout
```

If retries remain:

```
status → pending
retry_count += 1
push task_id back to queue
```

Else:

```
status → failed
error_message → timeout
```

---

# 4. Queue Architecture

Redis queues:

```
high_priority_queue
medium_priority_queue
low_priority_queue
```

Workers check queues in priority order.

Example:

```
pop(high)
if empty → pop(medium)
if empty → pop(low)
```

---

# 5. Worker Model

Model A: Fixed Workers

Example:

```
Worker1
Worker2
Worker3
Worker4
Worker5
```

Each worker processes one task at a time.

Scaling later:

```
docker-compose scale worker=10
```

---

# 6. Task Lifecycle

```
pending
   ↓
running
   ↓
completed
   OR
failed
```

Recovery path:

```
running (timeout)
   ↓
retrying
   ↓
pending
```

---

# 7. Database Design

Primary table: `tasks`

Fields:

```
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
```

Important notes:

* `payload` stores task parameters
* `result` stores task output
* JSONB used for flexibility
* `task_id` uses UUID for distributed safety

---

# 8. Task Payload Model

Example payloads:

Email task:

```
{
  "email": "user@test.com",
  "subject": "Hello"
}
```

Image task:

```
{
  "image_url": "...",
  "size": "1024x1024"
}
```

Validation handled by API using Pydantic models.

---

# 9. Reliability Mechanisms

### Task Claiming

Worker claims task using DB lock:

```
UPDATE tasks
SET status = 'running'
WHERE task_id = ?
AND status = 'pending'
```

Ensures only one worker processes a task.

---

### Processing Queue

When worker picks a task:

```
main_queue → processing_queue
```

Prevents lost tasks if worker crashes.

---

### Retry Mechanism

Tasks retry until:

```
retry_count >= max_retries
```

Then status becomes `failed`.

---

# 10. Repository Structure

Monorepo layout:

```
task-platform/

api_service/
  main.py

worker_service/
  main.py

recovery_service/
  main.py

shared/
  models/
  db/
  config/

docker/
docker-compose.yml
README.md
system-design.md
```

Each service runs independently.

---

# 11. Deployment Model

Docker Compose starts:

```
API Service
Worker Service
Recovery Service
Redis
PostgreSQL
```

Example:

```
docker-compose up
```

Workers can scale horizontally.

---

# 12. Development Roadmap

### Phase 1

API + Database

```
Client → API → DB
```

### Phase 2

Queue Integration

```
Client → API → DB → Redis
```

### Phase 3

Worker Execution

```
Client → API → DB → Redis → Worker
```

### Phase 4

Recovery Service

```
Client → API → DB → Redis → Worker
                      ↑
                 Recovery Service
```

---

# 13. Future Enhancements

Possible extensions:

* auto-scaling workers
* task scheduling
* metrics and monitoring
* distributed event system
* AI workload support
* multi-region queues

---

# 14. Learning Goals

This project demonstrates:

* asynchronous system design
* distributed workers
* queue-based architecture
* failure recovery
* retry logic
* scalable backend architecture
* production-style service structure
