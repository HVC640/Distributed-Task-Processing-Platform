# Engineering Decisions — Distributed Task Processing Platform

This document records the key architectural decisions made while designing the system and the reasoning behind them.

The goal is to document **why certain approaches were chosen**, not just what was implemented.

---

# 1. Task ID Generation

## Decision

Use **UUID** instead of auto-increment integer IDs.

## Reason

Advantages:

* globally unique across distributed systems
* no central coordination required
* prevents predictable task enumeration
* workers and services can generate IDs independently

Tradeoff:

* slightly larger storage size
* marginally slower indexing

For a distributed system, the benefits outweigh the costs.

---

# 2. Task Payload Storage

## Decision

Store task payloads using **JSONB** instead of structured columns.

Example:

```json
{
  "email": "user@test.com",
  "subject": "Hello"
}
```

## Reason

Advantages:

* supports many task types
* avoids schema modifications for new tasks
* enables flexible task payloads

Tradeoff:

* less strict schema enforcement

Mitigation:

* payload validation occurs at the API layer using Pydantic models.

---

# 3. Database First → Queue Later

## Decision

When a task is created:

```text
API → DB insert → push task_id to queue
```

## Reason

Advantages:

* ensures tasks are never lost
* enables status tracking
* supports rate limiting
* allows queue reconstruction if Redis fails

This pattern is used in many reliable background job systems.

---

# 4. Queue Technology

## Decision

Use **Redis queues**.

## Reason

Advantages:

* extremely fast
* simple queue operations
* supports blocking pops
* widely used in background job systems

Redis acts only as a **delivery mechanism**, while PostgreSQL stores task state.

---

# 5. Worker Task Fetch Strategy

## Decision

Use **blocking queue operations (BRPOP)**.

Example:

```text
BRPOP main_queue
```

## Reason

Advantages:

* no CPU wasted during idle periods
* instant task pickup
* avoids continuous polling

This is the most efficient worker consumption model.

---

# 6. Worker Concurrency Model

## Decision

Each worker processes **one task at a time**.

## Reason

Advantages:

* simple concurrency model
* prevents DB overload
* easier debugging
* predictable throughput

Future scaling can be achieved by increasing the number of worker instances.

---

# 7. Worker Scaling Strategy

## Decision

Use **fixed number of workers initially**.

Example:

```text
worker_1
worker_2
worker_3
worker_4
worker_5
```

## Reason

Advantages:

* simpler architecture
* easier debugging
* predictable load on database

Dynamic scaling will be introduced in later system versions.

---

# 8. Queue Priority Strategy

## Decision

Use **multiple queues instead of priority scoring**.

Example:

```text
high_priority_queue
medium_priority_queue
low_priority_queue
```

Workers check queues in priority order.

## Reason

Advantages:

* simpler implementation
* avoids starvation problems
* easier debugging
* common industry pattern

Using dynamic priority algorithms (like MLFQ) would introduce unnecessary complexity.

---

# 9. Worker Handler Strategy

## Decision

Use a **task handler registry**.

Example:

```python
TASK_HANDLERS = {
    "send_email": send_email_handler,
    "resize_image": resize_image_handler
}
```

## Reason

Advantages:

* explicit control over supported tasks
* safer execution
* easier debugging

Dynamic imports were avoided due to potential runtime risks.

---

# 10. Processing Queue Design

## Decision

When a worker receives a task:

```text
main_queue → processing_queue
```

## Reason

Advantages:

* prevents task loss if worker crashes
* enables recovery of stuck tasks
* easier monitoring of in-progress tasks

This pattern is used in many robust job processing systems.

---

# 11. Failure Recovery Strategy

## Decision

Introduce a **Recovery Service** that periodically checks for stuck tasks.

Example query:

```sql
SELECT *
FROM tasks
WHERE status = 'running'
AND started_at < now() - timeout
```

## Reason

Advantages:

* detects crashed workers
* requeues unfinished tasks
* prevents system deadlocks

This recovery mechanism ensures system reliability.

---

# 12. Repository Structure

## Decision

Use a **monorepo** structure.

Example:

```text
task-platform/
api_service/
worker_service/
recovery_service/
shared/
```

## Reason

Advantages:

* simpler development workflow
* shared utilities and models
* easier local testing
* consistent dependency management

Each service still runs independently.

---

# 13. Service Separation

## Decision

API, Worker, and Recovery services run independently.

## Reason

Advantages:

* loose coupling
* easier scaling
* independent deployment
* improved fault isolation

Distributed systems should avoid tightly coupled services.

---

# 14. Development Strategy

## Decision

Use **top-down development**.

Implementation order:

```text
API → Database → Queue → Worker → Recovery
```

## Reason

Advantages:

* faster testing
* clear system contracts
* easier debugging
* incremental development

---

# 15. JSON Payload Validation

## Decision

Use **Pydantic models in FastAPI** for validation.

Example:

```python
class EmailTask(BaseModel):
    email: str
    subject: str
```

## Reason

Advantages:

* ensures payload correctness
* prevents malformed tasks
* improves API reliability

---

# 16. Observability (Future)

Monitoring will later include:

* task execution time
* queue backlog
* worker utilization
* failure rate

This will allow system performance tuning.

---

# 17. Future Enhancements

Possible future improvements:

* dynamic worker scaling
* scheduled tasks
* distributed event streaming
* monitoring dashboards
* AI workload integration

These features will evolve as the system grows.

---

# Final Philosophy

The architecture follows these principles:

* reliability before complexity
* simple components with clear responsibilities
* failure recovery built into system design
* incremental system evolution

The goal is to build a **production-style backend system while maintaining simplicity during development**.
