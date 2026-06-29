# IV. Request Lifecycles

> *This document describes the request lifecycle of every API endpoint — how each coordinates the service layer, workers, and storage backends — together with the cross-cutting API conventions shared across them.*

## Scope & API Contracts

This document describes the **request lifecycles** — how each endpoint coordinates the service layer, workers, and storage backends — not the wire-level API contracts. Request and response schemas, field types, and status codes are deliberately omitted here to avoid duplicating a source of truth that would inevitably drift. For the exact contracts, consult the code itself, where every endpoint is fully annotated and documented through inline comments, or [export](../packages/scripts/src/scripts/utils/export_swagger.py) the OpenAPI (Swagger) specification and inspect it in any Swagger viewer (e.g. the online Swagger Editor).

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Explicit action suffixes for heavy operations** | Strict REST favors noun-only paths (`POST /videos`), but this API uses action suffixes (`/ingest`, `/submit`, `/download`) for operations that involve heavy I/O or background processing. These are genuinely long-running actions rather than plain resource writes, so naming the action is clearer and more honest about what happens than contorting it into a noun. A pragmatic deviation, accepted for readability over REST purity (**NFR‑8**). |
| **Uniform `201` on deduplicated submissions** | When a submission matches existing work, the service returns the already-created resource — still under `201 Created` rather than a distinct "already existed" code. Strictly this misreports whether anything was created, but the deviation is deliberate: it is simpler to implement, and clients are expected to act on the response *body* (the resource and its id), not to branch on fine-grained status codes. The contract stays predictable; only the create/reuse distinction is elided. |
| **Unified, generic error responses** | Per **NFR‑1**, the client is fully decoupled from the execution environment. Leaking internal details (stack traces, library exceptions, class names) would break that decoupling and couple clients to the service's internals. A centralized handler translates every internal exception into one consistent, generic error shape — protecting the internal architecture and giving clients a stable contract to handle regardless of what failed inside. |

## Endpoint Lifecycles

### `GET /health/shallow/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    C->>S: GET /health/shallow/
    S-->>C: 200 OK
```

### `GET /health/deep/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant MB as Message Broker
    participant O as Object Storage (S3)
    C->>S: GET /health/deep/
    par
        S->>DB: test query
        S->>MB: broker health probe
        S->>O: bucket access probe
    end
    S-->>C: 200 OK
```

### `POST /videos/ingest/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
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

### `GET /videos/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    C->>S: GET /videos/
    S->>DB: fetch paginated video records
    S-->>C: 200 OK
```

### `GET /videos/{video_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    C->>S: GET /videos/{video_id}/
    S->>DB: fetch video record by ID
    S-->>C: 200 OK
```

### `GET /videos/download/{video_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
    C->>S: GET /videos/download/{video_id}/
    S->>DB: fetch video record by ID
    S->>O: download video file
    S-->>C: 200 OK (raw bytes)
```

### `DELETE /videos/{video_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
    C->>S: DELETE /videos/{video_id}/
    S->>DB: fetch dependent storage keys
    S->>DB: delete video record (cascades to estimations and visualizations)
    S->>O: delete all dependent artifacts
    S-->>C: 204 No Content
```

### `GET /tasks/{task_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant RB as Result Backend
    C->>S: GET /tasks/{task_id}/
    S->>RB: query task state by ID
    S-->>C: 200 OK
```

### `POST /estimations/submit/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant RB as Result Backend
    participant MB as Message Broker
    participant W as Inference Worker
    participant O as Object Storage (S3)

    C->>S: POST /estimations/submit/
    S->>DB: verify source video exists
    S->>RB: register task (Status: PENDING)
    S->>MB: enqueue inference task
    S-->>C: 202 Accepted (task_id)

    W->>MB: dequeue task
    W->>RB: update task (Status: PROCESSING)
    W->>W: check params hash for duplicate

    alt duplicate found
        W->>DB: fetch existing estimation record
        W->>RB: update task (Status: COMPLETED, result: record_id)
    else new estimation
        W->>O: download video file
        W->>W: run ensam3d_inference pipeline
        W->>O: upload safetensors archive
        W->>DB: create estimation record
        W->>RB: update task (Status: COMPLETED, result: record_id)
    end
    W->>MB: acknowledge task completion
```

### `GET /estimations/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    C->>S: GET /estimations/
    S->>DB: fetch paginated estimation records
    S-->>C: 200 OK
```

### `GET /estimations/{estimation_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    C->>S: GET /estimations/{estimation_id}/
    S->>DB: fetch estimation record by ID
    S-->>C: 200 OK
```

### `GET /estimations/download/{estimation_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
    C->>S: GET /estimations/download/{estimation_id}/
    S->>DB: fetch estimation record by ID
    S->>O: download safetensors archive
    S-->>C: 200 OK (raw bytes)
```

### `DELETE /estimations/{estimation_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
    C->>S: DELETE /estimations/{estimation_id}/
    S->>DB: fetch dependent storage keys
    S->>DB: delete estimation record (cascades to visualizations)
    S->>O: delete all dependent artifacts
    S-->>C: 204 No Content
```

### `POST /visualizations/submit/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant RB as Result Backend
    participant MB as Message Broker
    participant W as Post-processing Worker
    participant O as Object Storage (S3)

    C->>S: POST /visualizations/submit/
    S->>DB: verify source estimation and video exist
    S->>RB: register task (Status: PENDING)
    S->>MB: enqueue visualization task
    S-->>C: 202 Accepted (task_id)

    W->>MB: dequeue task
    W->>RB: update task (Status: PROCESSING)
    W->>W: check params hash for duplicate

    alt duplicate found
        W->>DB: fetch existing visualization record
        W->>RB: update task (Status: COMPLETED, result: record_id)
    else new visualization
        W->>O: download video file and safetensors archive
        W->>W: render annotated video
        W->>O: upload rendered MP4 file
        W->>DB: create visualization record
        W->>RB: update task (Status: COMPLETED, result: record_id)
    end
    W->>MB: acknowledge task completion
```

### `GET /visualizations/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    C->>S: GET /visualizations/
    S->>DB: fetch paginated visualization records
    S-->>C: 200 OK
```

### `GET /visualizations/{visualization_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    C->>S: GET /visualizations/{visualization_id}/
    S->>DB: fetch visualization record by ID
    S-->>C: 200 OK
```

### `GET /visualizations/download/{visualization_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
    C->>S: GET /visualizations/download/{visualization_id}/
    S->>DB: fetch visualization record by ID
    S->>O: download rendered MP4 file
    S-->>C: 200 OK (raw bytes)
```

### `DELETE /visualizations/{visualization_id}/`

```mermaid
sequenceDiagram
    actor C as Client
    participant S as Service Layer
    participant DB as SQL Database
    participant O as Object Storage (S3)
    C->>S: DELETE /visualizations/{visualization_id}/
    S->>DB: fetch visualization storage key
    S->>DB: delete visualization record
    S->>O: delete rendered MP4 file
    S-->>C: 204 No Content
```