# VII. **Request Flows**

> *This document defines the runtime interaction patterns through sequence diagrams, making the execution flow and inter-component communication explicit for each API operation.*

The following diagrams detail how client requests traverse the service layer, interact with persistent storage, and coordinate with background workers. Each flow demonstrates the strict separation between synchronous HTTP handling (Service Layer) and asynchronous task execution (Workers), as well as the content-addressed deduplication strategy that prevents redundant processing and storage.

## `GET /health/shallow/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    C->>S: GET /health/shallow/
    S-->>C: 200 OK
```

## `GET /health/deep/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant Q as Task Queue
    participant O as Object Storage
    C->>S: GET /health/deep/
    par
        S->>DB: test query
        S->>Q: broker health probe
        S->>O: bucket access probe
    end
    S-->>C: 200 OK
```

## `POST /videos/ingest/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage
    C->>S: POST /videos/ingest/ (video file)
    S->>S: validate content type & extract metadata
    S->>DB: check content hash for duplicate
    alt duplicate found
        S-->>C: 201 Created (existing record)
    else new video
        S->>O: upload video file
        S->>DB: create video record
        S-->>C: 201 Created
    end
```

## `GET /videos/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store

    C->>S: GET /videos/
    S->>DB: fetch paginated video records
    S-->>C: 200 OK
```

## `GET /videos/{video_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store

    C->>S: GET /videos/{video_id}/
    S->>DB: fetch video record by ID
    S-->>C: 200 OK
```

## `GET /videos/download/{video_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage

    C->>S: GET /videos/download/{video_id}/
    S->>DB: fetch video record by ID
    S->>O: download video file
    S-->>C: 200 OK (raw bytes)
```

## `DELETE /videos/{video_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage

    C->>S: DELETE /videos/{video_id}/
    S->>DB: fetch dependent storage keys
    S->>DB: delete video record (cascades to estimations and visualizations)
    S->>O: delete all dependent artifacts
    S-->>C: 204 No Content
```

## `GET /tasks/{task_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant SS as State Store
    
    C->>S: GET /tasks/{task_id}/
    S->>SS: query task state by ID
    S-->>C: 200 OK
```

## `POST /estimations/submit/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant SS as State Store
    participant Q as Task Queue
    participant W as Inference Worker
    participant O as Object Storage

    C->>S: POST /estimations/submit/
    S->>DB: verify source video exists
    S->>SS: register task (Status: PENDING)
    S->>Q: enqueue inference task
    S-->>C: 202 Accepted (task_id)
    
    Q->>W: dispatch task
    W->>SS: update task (Status: PROCESSING)
    W->>W: check params hash for duplicate
    
    alt duplicate found
        W->>DB: fetch existing estimation record
        W->>SS: update task (Status: COMPLETED, result: record_id)
    else new estimation
        W->>O: download video file
        W->>W: run ensam3d_inference pipeline
        W->>O: upload safetensors archive
        W->>DB: create estimation record
        W->>SS: update task (Status: COMPLETED, result: record_id)
    end
    W->>Q: acknowledge task completion
```

## `GET /estimations/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store

    C->>S: GET /estimations/
    S->>DB: fetch paginated estimation records
    S-->>C: 200 OK
```

## `GET /estimations/{estimation_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store

    C->>S: GET /estimations/{estimation_id}/
    S->>DB: fetch estimation record by ID
    S-->>C: 200 OK
```

## `GET /estimations/download/{estimation_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage

    C->>S: GET /estimations/download/{estimation_id}/
    S->>DB: fetch estimation record by ID
    S->>O: download safetensors archive
    S-->>C: 200 OK (raw bytes)
```

## `DELETE /estimations/{estimation_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage

    C->>S: DELETE /estimations/{estimation_id}/
    S->>DB: fetch dependent storage keys
    S->>DB: delete estimation record (cascades to visualizations)
    S->>O: delete all dependent artifacts
    S-->>C: 204 No Content
```

## `POST /visualizations/submit/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant SS as State Store
    participant Q as Task Queue
    participant W as Post-processing Worker
    participant O as Object Storage

    C->>S: POST /visualizations/submit/
    S->>DB: verify source estimation and video exist
    S->>SS: register task (Status: PENDING)
    S->>Q: enqueue visualization task
    S-->>C: 202 Accepted (task_id)
    
    Q->>W: dispatch task
    W->>SS: update task (Status: PROCESSING)
    W->>W: check params hash for duplicate
    
    alt duplicate found
        W->>DB: fetch existing visualization record
        W->>SS: update task (Status: COMPLETED, result: record_id)
    else new visualization
        W->>O: download video file and safetensors archive
        W->>W: render annotated video
        W->>O: upload rendered MP4 file
        W->>DB: create visualization record
        W->>SS: update task (Status: COMPLETED, result: record_id)
    end
    W->>Q: acknowledge task completion
```

## `GET /visualizations/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store

    C->>S: GET /visualizations/
    S->>DB: fetch paginated visualization records
    S-->>C: 200 OK
```

## `GET /visualizations/{visualization_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store

    C->>S: GET /visualizations/{visualization_id}/
    S->>DB: fetch visualization record by ID
    S-->>C: 200 OK
```

## `GET /visualizations/download/{visualization_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage

    C->>S: GET /visualizations/download/{visualization_id}/
    S->>DB: fetch visualization record by ID
    S->>O: download rendered MP4 file
    S-->>C: 200 OK (raw bytes)
```

## `DELETE /visualizations/{visualization_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as API Server
    participant DB as Metadata Store
    participant O as Object Storage

    C->>S: DELETE /visualizations/{visualization_id}/
    S->>DB: fetch visualization storage key
    S->>DB: delete visualization record
    S->>O: delete rendered MP4 file
    S-->>C: 204 No Content
```

## Next Steps

With the complete runtime interaction patterns formally documented, the Request Flows section is complete. Every API operation now has an explicit sequence diagram showing the exact order of interactions between the client, API server, metadata store, state store, task queue, inference workers, and object storage.

These diagrams serve as the definitive operational specification for the Human Pose Estimation Service. They provide:

1. **Implementation clarity**: Developers can trace the exact execution path for every endpoint, including error handling branches, deduplication logic, and asynchronous task lifecycle management.

2. **Operational observability**: Infrastructure teams can identify which components participate in each flow, enabling targeted monitoring, alerting, and capacity planning.

3. **Debugging reference**: When issues arise in production, these diagrams provide a baseline for comparing expected versus actual behavior, making root cause analysis more systematic.

4. **Testing strategy**: QA engineers can derive integration test scenarios directly from these flows, ensuring that all branches (success paths, duplicate detection, failure modes) are covered.

The documentation now spans the full architectural stack: from high-level conceptual design and runtime concurrency models, through domain entity schemas and API contracts, down to the exact sequence of inter-component messages that execute at runtime.

The next document will formalize the **Dependencies and Technology Stack**, mapping the abstract architectural roles defined throughout this documentation (Task Queue, State Store, Metadata Store, Object Storage) to concrete, battle-tested open-source technologies. This final piece of the architectural puzzle will provide the exact blueprint required to build, deploy, and operate the system in both local development and production environments.