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
* safe across multiple services

Tradeoff:

* slightly larger storage size
* marginally slower indexing

For distributed systems, UUID provides stronger guarantees.

---

# 2. Task Payload Storage

## Decision

Store task payloads using **JSONB**.

## Reason

Advantages:

* supports multiple task types
* avoids schema changes
* flexible structure

Tradeoff:

* weaker schema enforcement

Mitigation:

* strict validation at API layer using Pydantic

---

# 3. Database Before Queue

## Decision

```text
API → DB insert → push task_id to queue
```

## Reason

Advantages:

* prevents task loss
* enables state tracking
* supports recovery
* ensures system consistency

This follows the principle:

> **DB = source of truth, queue = delivery mechanism**

---

# 4. Queue Technology

## Decision

Use **Redis**.

## Reason

Advantages:

* high throughput
* supports blocking operations
* simple and efficient
* widely adopted

Redis is used as:

* task queue
* metrics store
* rate limiter backend

---

# 5. Worker Fetch Strategy

## Decision

Use **BRPOP (blocking queue)**.

## Reason

Advantages:

* no CPU wastage
* instant task pickup
* efficient idle handling

---

# 6. Worker Concurrency Model

## Decision

One task per worker.

## Reason

Advantages:

* simple execution model
* predictable load
* easier debugging
* avoids resource contention

Scaling is achieved horizontally.

---

# 7. Worker Scaling Strategy

## Decision

Horizontal scaling using multiple workers.

```text
docker-compose up --scale worker=N
```

## Reason

Advantages:

* linear scalability
* no shared state between workers
* aligns with distributed systems

---

# 8. Queue Priority Strategy

## Decision

Use **multiple priority queues**.

```text
high / medium / low
```

## Reason

Advantages:

* simple implementation
* avoids complex scheduling logic
* predictable execution order

Rejected:

* dynamic priority algorithms (too complex for current scope)

---

# 9. Task Handler Strategy

## Decision

Use **explicit handler registry**.

```python
TASK_HANDLERS = {...}
```

## Reason

Advantages:

* safe execution
* controlled behavior
* avoids dynamic execution risks

---

# 10. Processing Model

## Decision

Workers directly process tasks after queue fetch.

## Reason

* reduces system complexity
* avoids unnecessary intermediate layers
* keeps execution flow simple

---

# 11. Lease-Based Ownership Model

## Decision

Use **lease + worker_id** instead of relying only on status.

## Reason

Problem:

* worker crash leads to stuck tasks
* duplicate execution risk

Solution:

* worker acquires task with lease
* lease expires if worker dies

Advantages:

* prevents indefinite locking
* enables safe recovery
* works well in distributed systems

---

# 12. Heartbeat Mechanism

## Decision

Workers periodically update:

```text
last_heartbeat
lease_expires_at
```

## Reason

Advantages:

* tracks worker liveness
* prevents premature recovery
* supports long-running tasks

---

# 13. Recovery Strategy

## Decision

Use a **Recovery Service based on lease expiration**.

```sql
WHERE lease_expires_at < now()
```

## Reason

Advantages:

* detects dead workers
* requeues orphaned tasks
* ensures system continuity

Rejected:

* started_at-based recovery (inaccurate for long tasks)

---

# 14. At-Least-Once Execution Model

## Decision

Accept **at-least-once execution**.

## Reason

* simpler to implement
* practical in distributed systems
* avoids heavy coordination

Tradeoff:

* possible duplicate execution

Mitigation:

* idempotent task design
* ownership validation

---

# 15. Ownership Validation

## Decision

Worker verifies ownership before updating DB.

## Reason

Prevents:

* stale workers overwriting results
* race conditions

---

# 16. Observability — Logging

## Decision

Use **structured JSON logging via stdout**.

## Reason

Advantages:

* centralized via Docker
* easy integration with log systems
* machine-readable

Rejected:

* file-based logging (not scalable in containers)

---

# 17. Observability — Metrics

## Decision

Use **Redis-based metrics**.

## Reason

Advantages:

* low latency
* simple implementation
* real-time visibility

Tradeoff:

* non-persistent

Accepted for current scope.

---

# 18. Rate Limiting Strategy

## Decision

Use **Token Bucket algorithm with Redis + Lua**.

## Reason

Advantages:

* supports burst traffic
* smooth rate limiting
* atomic (Lua script)
* distributed safe

Rejected:

* fixed window (inaccurate)
* sliding window (more complex)

---

# 19. Repository Structure

## Decision

Use **monorepo**.

## Reason

Advantages:

* shared code reuse
* consistent structure
* easier local development

---

# 20. Service Separation

## Decision

Separate services:

* API
* Worker
* Recovery

## Reason

Advantages:

* loose coupling
* independent scaling
* fault isolation

---

# 21. Development Strategy

## Decision

Top-down development.

```text
API → DB → Queue → Worker → Recovery → Observability
```

## Reason

Advantages:

* faster validation
* incremental complexity
* easier debugging

---

# 22. Deployment Strategy

## Decision

Use **Docker Compose**.

## Reason

Advantages:

* reproducible environment
* easy local deployment
* service isolation

---

# 23. System Tradeoffs

| Area      | Choice        | Tradeoff                            |
| --------- | ------------- | ----------------------------------- |
| Execution | At-least-once | duplicates possible                 |
| Metrics   | Redis         | non-persistent                      |
| Logging   | stdout        | requires external tools for scaling |
| Queue     | Redis         | not durable like Kafka              |

---

# Final Philosophy

The system follows:

* simplicity over premature complexity
* reliability over optimization
* clear ownership model
* observable system design
* incremental evolution

The goal is to build a **production-style distributed system while maintaining clarity and control**.

---
