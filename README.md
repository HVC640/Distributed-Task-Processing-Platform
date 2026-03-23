# 🚀 Distributed Task Processing Platform

A **production-style distributed background job processing system** built using **FastAPI, Redis, PostgreSQL, and Docker**.

This system is designed to simulate real-world architectures used in:

* Celery / Sidekiq
* AWS SQS worker pipelines
* Distributed job schedulers

---

# 📌 Problem Statement

Modern applications require handling tasks such as:

* sending emails
* processing images
* running background computations

These tasks should not block API responses and must be:

* asynchronous
* reliable
* scalable
* fault-tolerant

This project solves this by building a **distributed task execution platform from scratch**.

---

# 🧠 Key Features

### ✅ Distributed Task Processing

* Multiple workers process tasks asynchronously
* Horizontal scaling supported

---

### ✅ Priority-Based Queues

* High / Medium / Low priority queues
* Workers consume in priority order

---

### ✅ Lease-Based Execution Model

* Tasks are owned via **lease + worker_id**
* Prevents duplicate execution and stuck tasks

---

### ✅ Heartbeat Mechanism

* Workers continuously update liveness
* Supports long-running tasks

---

### ✅ Automatic Failure Recovery

* Recovery service detects **expired leases**
* Requeues orphaned tasks safely

---

### ✅ At-Least-Once Execution Guarantee

* Ensures reliability
* Accepts controlled duplication (industry standard tradeoff)

---

### ✅ Observability (Production Style)

* Structured JSON logging
* Real-time system metrics

---

### ✅ API Rate Limiting

* Token Bucket algorithm
* Redis + Lua (atomic, distributed-safe)

---

### ✅ Fully Dockerized

* Multi-service architecture
* Easy local deployment

---

# 🏗️ Architecture Overview

```text
Client → API → PostgreSQL → Redis → Workers → Execution
                             ↑
                        Recovery Service
```

* **PostgreSQL** → Source of truth (task state)
* **Redis** → Queue + Metrics + Rate Limiting
* **Workers** → Execute tasks
* **Recovery Service** → Ensures reliability

---

# ⚙️ Tech Stack

| Component        | Technology         |
| ---------------- | ------------------ |
| API              | FastAPI            |
| Queue            | Redis              |
| Database         | PostgreSQL         |
| Workers          | Python             |
| Containerization | Docker             |
| Observability    | Logging + Metrics  |
| Rate Limiting    | Redis (Lua Script) |

---

# 🔄 Task Lifecycle

```text
pending → running → completed
                 ↘ failed
```

Recovery flow:

```text
running + lease expired → retry → pending
```

---

# 🧩 System Highlights

### 🔹 Lease + Heartbeat Model

* Prevents stale workers from corrupting state
* Enables safe distributed execution

---

### 🔹 Ownership Validation

* Worker verifies ownership before updating DB
* Eliminates race conditions

---

### 🔹 Fault Tolerance

* Worker crash → task automatically recovered
* No task loss

---

### 🔹 Horizontal Scaling

```bash
docker-compose up --scale worker=5
```

---

# 📊 Metrics Exposed

```text
tasks_created
tasks_completed
tasks_failed
tasks_retried
avg_execution_time
tasks_in_queue
```

Endpoint:

```text
GET /metrics
```

---

# 🛡️ Rate Limiting

* Token Bucket algorithm
* Supports burst traffic
* Prevents API abuse

---

# 📂 Project Structure

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

docker-compose.yml
system-design.md
architecture-diagram.md
engineering-decisions.md
```

---

# 🚀 Getting Started

## 1. Clone Repository

```bash
git clone <your-repo-url>
cd task-platform
```

---

## 2. Start System

```bash
docker-compose up --build
```

---

## 3. Create a Task

```json
POST /tasks
{
    "task_type": "send_email",
    "priority": "low"
}
```

---

## 4. Check Metrics

```text
GET /metrics
```

---

# 🧪 Example Failure Scenario

1. Submit a long-running task
2. Kill worker container

```bash
docker kill <worker_container>
```

3. Observe:

```text
Lease expires → Recovery triggers → Task re-executed
```

---

# 🎯 System Guarantees

| Property                           | Status |
| ---------------------------------- | ------ |
| At-least-once execution            | ✅      |
| Fault tolerance                    | ✅      |
| Horizontal scalability             | ✅      |
| Duplicate prevention (best-effort) | ✅      |
| Exactly-once execution             | ❌      |

---

# ⚖️ Design Tradeoffs

* Chose **at-least-once execution** over complexity
* Used **Redis for simplicity** (instead of Kafka)
* Metrics are **non-persistent (Redis-based)**
* Logging via **stdout for container compatibility**

---

# 📚 What I Learned

This project demonstrates:

* distributed system design
* lease-based execution model
* fault tolerance & recovery
* queue-based architectures
* observability (logs + metrics)
* rate limiting strategies
* production-style backend engineering

---

# 🔮 Future Improvements

* Kafka-based event system
* Prometheus + Grafana metrics
* ELK stack logging
* Auto-scaling workers
* Task scheduling (cron)
* Multi-region support

---

# 🙌 Final Note

This project is built to **simulate real-world backend systems**, focusing on:

> reliability, scalability, and production-grade thinking

---
