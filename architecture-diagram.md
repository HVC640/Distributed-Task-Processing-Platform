# Architecture Diagrams — Distributed Task Processing Platform

This document contains visual architecture diagrams.

These diagrams complement `system-design.md`.

---

# 1. High-Level System Architecture

```mermaid
flowchart TD

Client --> API[FastAPI API Service]

API --> DB[(PostgreSQL)]
API --> Redis[(Redis: Queue + Metrics + Rate Limiting)]

Redis --> Worker1[Worker Service 1]
Redis --> Worker2[Worker Service 2]
Redis --> WorkerN[Worker Service N]

Worker1 --> DB
Worker2 --> DB
WorkerN --> DB

Recovery[Recovery Service] --> DB
Recovery --> Redis
```

Description:

* API handles requests and enforces rate limiting
* PostgreSQL stores task state and ownership
* Redis acts as queue + metrics store + rate limiter backend
* Workers process tasks with lease + heartbeat
* Recovery service ensures fault tolerance

---

# 2. Task Creation Flow (With Rate Limiting)

```mermaid
sequenceDiagram

participant Client
participant API
participant Redis
participant DB

Client->>API: POST /tasks
API->>Redis: Check rate limit (Token Bucket)

alt Allowed
    API->>DB: Insert task (status=pending)
    API->>Redis: Push task_id to priority queue
    API->>Redis: Increment metrics
    API-->>Client: task_id
else Rate Limited
    API-->>Client: 429 Too Many Requests
end
```

---

# 3. Worker Execution Flow (Lease + Heartbeat)

```mermaid
sequenceDiagram

participant Worker
participant Redis
participant DB

Worker->>Redis: BRPOP(priority queues)
Redis-->>Worker: task_id

Worker->>DB: Claim task (lease + worker_id)
Worker->>Worker: Start heartbeat thread

Worker->>Worker: Execute handler(payload)

Worker->>DB: Validate ownership
Worker->>DB: Update status (COMPLETED / FAILED)

Worker->>Worker: Stop heartbeat
```

Key Concepts:

* Lease-based ownership
* Heartbeat for liveness
* Ownership validation prevents stale updates

---

# 4. Lease & Heartbeat Mechanism

```mermaid
flowchart TD

Worker --> ClaimTask[Claim Task with Lease]
ClaimTask --> StartHeartbeat[Start Heartbeat Loop]

StartHeartbeat --> UpdateLease[Update lease_expires_at periodically]

UpdateLease -->|Worker Alive| ContinueExecution
UpdateLease -->|Worker Dead| LeaseExpires

LeaseExpires --> RecoveryTriggered[Recovery Service Picks Task]
```

---

# 5. Worker Failure & Recovery

```mermaid
sequenceDiagram

participant Worker
participant DB
participant Recovery
participant Redis

Worker->>DB: status=RUNNING (lease active)

Worker--xWorker: Crash

Recovery->>DB: Find tasks where lease_expires_at < now()

Recovery->>DB: Clear ownership + increment retry
Recovery->>Redis: Requeue task
```

This ensures:

* no stuck tasks
* safe retry mechanism
* fault tolerance

---

# 6. Queue Architecture (Priority-Based)

```mermaid
flowchart TD

High[High Priority Queue]
Medium[Medium Priority Queue]
Low[Low Priority Queue]

Worker --> High
Worker --> Medium
Worker --> Low
```

Worker fetch logic:

1. High priority
2. Medium priority
3. Low priority

---

# 7. Task Lifecycle

```mermaid
stateDiagram-v2

[*] --> pending
pending --> running : lease acquired
running --> completed
running --> failed

running --> retrying : lease expired
retrying --> pending
```

---

# 8. Observability Architecture

```mermaid
flowchart TD

API --> Logs[Structured Logs]
Worker --> Logs
Recovery --> Logs

API --> Metrics[Redis Metrics]
Worker --> Metrics
Recovery --> Metrics
```

Description:

* Logs are structured (JSON) and emitted to stdout
* Metrics are stored in Redis
* Provides system visibility and debugging

---

# 9. Rate Limiting Architecture

```mermaid
flowchart TD

Client --> API
API --> RedisRateLimiter[Redis Token Bucket]

RedisRateLimiter -->|Allowed| ProcessRequest
RedisRateLimiter -->|Rejected| Reject429
```

Features:

* Token bucket algorithm
* Distributed-safe (Lua script)
* Burst handling

---

# 10. Service Deployment Layout

```mermaid
flowchart LR

subgraph Application
API
Worker
Recovery
end

subgraph Infrastructure
Redis
Postgres
end

API --> Redis
API --> Postgres

Worker --> Redis
Worker --> Postgres

Recovery --> Postgres
Recovery --> Redis
```

---

# 11. Worker Internal Flow

```mermaid
flowchart TD

Start --> FetchTask
FetchTask --> ClaimTask
ClaimTask --> StartHeartbeat

StartHeartbeat --> ExecuteHandler

ExecuteHandler --> Success
ExecuteHandler --> Failure

Success --> ValidateOwnership
Failure --> ValidateOwnership

ValidateOwnership --> UpdateDB
UpdateDB --> StopHeartbeat
StopHeartbeat --> Done
```

---

# 12. Scaling Model

```mermaid
flowchart TD

RedisQueue --> Worker1
RedisQueue --> Worker2
RedisQueue --> Worker3
RedisQueue --> WorkerN
```

Scaling example:

```
docker-compose up --scale worker=10
```

---

# 13. Design Principles

* asynchronous processing
* distributed workers
* lease-based ownership model
* fault tolerance via recovery service
* stateless worker design
* observability (logs + metrics)
* API protection (rate limiting)

---
