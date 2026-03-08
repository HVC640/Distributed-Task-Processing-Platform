\# Architecture Diagrams — Distributed Task Processing Platform



This document contains visual architecture diagrams used for understanding and implementing the system.



These diagrams complement `system-design.md`.



---



\# 1. High-Level System Architecture



This shows the major services and their interactions.



```mermaid

flowchart TD



Client --> API\[FastAPI API Service]



API --> DB\[(PostgreSQL)]

API --> Redis\[(Redis Queue)]



Redis --> Worker1\[Worker Service 1]

Redis --> Worker2\[Worker Service 2]

Redis --> Worker3\[Worker Service N]



Worker1 --> DB

Worker2 --> DB

Worker3 --> DB



Recovery\[Recovery Service] --> DB

Recovery --> Redis

```



Description:



\* Client sends requests to API

\* API stores tasks in PostgreSQL

\* API pushes task IDs to Redis

\* Workers consume tasks from Redis

\* Workers update results in PostgreSQL

\* Recovery service monitors stuck tasks



---



\# 2. Task Creation Flow



```mermaid

sequenceDiagram



participant Client

participant API

participant DB

participant Redis



Client->>API: POST /tasks

API->>DB: Insert task (status=pending)

API->>Redis: Push task\_id to main\_queue

API-->>Client: task\_id response

```



Key idea:



API defines the \*\*system contract\*\*.



---



\# 3. Worker Execution Flow



```mermaid

sequenceDiagram



participant Worker

participant Redis

participant DB



Worker->>Redis: BRPOP main\_queue

Redis-->>Worker: task\_id



Worker->>Redis: Move task to processing\_queue



Worker->>DB: UPDATE tasks SET status='running'



Worker->>Worker: Execute handler(payload)



Worker->>DB: UPDATE tasks SET completed

Worker->>Redis: Remove from processing\_queue

```



Important concepts:



\* blocking queue

\* task claiming

\* execution tracking



---



\# 4. Worker Failure Scenario



```mermaid

sequenceDiagram



participant Worker

participant Redis

participant DB

participant Recovery



Worker->>Redis: BRPOP task

Worker->>DB: status=running



Worker--xWorker: Crash



Recovery->>DB: Find stuck tasks

Recovery->>Redis: Push task\_id back to queue

Recovery->>DB: retry\_count++

```



This prevents \*\*lost tasks\*\*.



---



\# 5. Queue Architecture



Workers consume tasks using \*\*priority queues\*\*.



```mermaid

flowchart TD



RedisHigh\[Redis High Queue]

RedisMedium\[Redis Medium Queue]

RedisLow\[Redis Low Queue]



Worker --> RedisHigh

Worker --> RedisMedium

Worker --> RedisLow

```



Worker priority order:



1\. High queue

2\. Medium queue

3\. Low queue



---



\# 6. Task Lifecycle



```mermaid

stateDiagram-v2



\[\*] --> pending

pending --> running

running --> completed

running --> failed

running --> retrying

retrying --> pending

```



---



\# 7. Service Deployment Layout



Services run independently but share infrastructure.



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



\# 8. Worker Internal Flow



```mermaid

flowchart TD



Start --> FetchTask

FetchTask --> ClaimTask

ClaimTask --> ExecuteHandler

ExecuteHandler --> Success

ExecuteHandler --> Failure



Success --> UpdateCompleted

Failure --> RetryLogic



RetryLogic --> Pending

UpdateCompleted --> Done

```



---



\# 9. Repository Structure



```mermaid

flowchart TD



Repo\[task-platform]



Repo --> APIService

Repo --> WorkerService

Repo --> RecoveryService

Repo --> Shared

Repo --> Docker

Repo --> Docs



Shared --> Models

Shared --> DB

Shared --> Config

```



---



\# 10. Scaling Model



Workers scale horizontally.



```mermaid

flowchart TD



RedisQueue --> Worker1

RedisQueue --> Worker2

RedisQueue --> Worker3

RedisQueue --> Worker4

RedisQueue --> WorkerN

```



Scaling example:



```

docker-compose up --scale worker=10

```



---



\# 11. Future Architecture Evolution



Possible future architecture:



```mermaid

flowchart TD



API --> Redis

API --> DB



Redis --> WorkerCluster



WorkerCluster --> Kafka

WorkerCluster --> AIService

WorkerCluster --> Storage



Monitoring --> WorkerCluster

Monitoring --> API

```



Future additions:



\* event streaming

\* AI inference

\* metrics dashboards

\* distributed scaling



---



\# 12. Design Principles Used



Key architecture principles used in this system:



\* asynchronous processing

\* queue-based workload distribution

\* worker horizontal scaling

\* failure recovery mechanisms

\* service isolation

\* stateless worker design



These principles mirror many real distributed systems.



