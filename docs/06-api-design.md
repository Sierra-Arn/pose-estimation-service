# VI. **API Design**

> *This document defines the external HTTP interface, resource mapping, and interaction patterns of the Human Pose Estimation Service.*

## Overview

The API serves as the strict boundary between external clients and the internal execution environment. It translates the conceptual input–output contract defined in the system overview into a concrete, network-accessible interface. 

The design prioritizes predictability, decoupling, and alignment with the asynchronous nature of the underlying inference workloads. Clients interact with the system exclusively through stateless HTTP requests, remaining entirely agnostic to the internal concurrency models, GPU resource management, and storage backends.

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **REST as the API architectural style** | The service has a natural domain model centered around processing jobs: a client submits a video, the service tracks the processing state, and the client eventually retrieves the result. REST provides a clean, resource-oriented mapping for this domain: jobs (`/jobs`), individual job state (`/jobs/{id}`), and job results (`/jobs/{id}/result`). The standard HTTP verbs (POST to create, GET to read) provide well-defined semantics that make the API cacheable, predictable, and easy to integrate with. If GraphQL were chosen, it would add schema and resolver complexities without benefit, since the response shape is fixed and known upfront. RPC-style endpoints (e.g., `/processVideo`, `/getResult`) would blur resource boundaries and make the API harder to reason about, test, and cache. |
| **Explicit action suffixes for heavy operations** | While strict REST dictates noun-only resource paths (e.g., `POST /videos`), this API uses explicit action suffixes (`/ingest`, `/submit`, `/download`) for operations involving heavy I/O or background processing. This pragmatic deviation from pure REST serves a critical operational purpose: it allows API Gateways, load balancers, and monitoring tools to apply distinct routing rules, timeout policies, and rate limits to heavy payloads versus standard metadata CRUD operations. |
| **Unified error handling with generic error responses** | The contract states that *«the client interacts with the system exclusively through network requests and remains fully decoupled from the execution environment»*. Exposing internal implementation details (stack traces, specific library exceptions, internal class names) would violate this decoupling and create tight coupling to the service's internal architecture. Implementing centralized error handlers that translate internal exceptions into a consistent, generic format (e.g., "resource not found", "invalid file type", "processing failed") preserves the decoupling, protects the internal architecture, and provides a predictable API contract that clients can reliably handle regardless of what failed inside the service. |


## Endpoint Specification

The API is organized around the core domain entities defined in the Domain Model. All state-mutating operations that trigger heavy background processing (inference or rendering) follow the **Submit-and-Poll** pattern, returning a `202 Accepted` status and a task identifier for asynchronous tracking.

### Health Probes

Designed for infrastructure orchestrators (e.g., Kubernetes, load balancers) to monitor service availability and dependency health.

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `GET` | `/health/shallow/` | `200 OK` | Lightweight liveness probe. Returns immediately without inspecting external dependencies. Designed for orchestrator liveness checks. |
| `GET` | `/health/deep/` | `200 OK` | Readiness probe. Concurrently checks reachability of the metadata database, message broker, and object storage. Returns an aggregated status: `ok` if all dependencies are reachable, `degraded` otherwise. Times out after a configurable threshold. |

### Video Assets — `/videos`

Manages the ingestion, retrieval, and lifecycle of raw video files.

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/videos/ingest/` | `201 Created` | Upload a video file via multipart form. Validates content, extracts metadata, uploads to object storage, and registers the asset. Returns the existing record if the content hash matches a duplicate (content-addressed deduplication). |
| `GET` | `/videos/` | `200 OK` | Retrieve a paginated list of video records ordered by primary key. Supports `skip` and `limit` query parameters. |
| `GET` | `/videos/{video_id}/` | `200 OK` | Retrieve technical specifications, storage location, and optional label for a specific video record. |
| `GET` | `/videos/download/{video_id}/` | `200 OK` | Download the raw video file as `application/octet-stream`. |
| `DELETE` | `/videos/{video_id}/` | `204 No Content` | Delete the video record and cascade-remove all associated estimation results, visualization outputs, and their corresponding object storage artifacts. |

### Estimation Jobs — `/estimations`

Manages the submission and retrieval of 3D pose estimation tasks.

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/estimations/submit/` | `202 Accepted` | Submit a 3D pose estimation task. Validates the source video record and enqueues the inference pipeline. Returns a `TaskResponse` for polling. Deduplication and storage key generation are performed within the worker. |
| `GET` | `/estimations/` | `200 OK` | Retrieve a paginated list of estimation records ordered by primary key. Supports `skip` and `limit` query parameters. |
| `GET` | `/estimations/{estimation_id}/` | `200 OK` | Retrieve pipeline parameters, storage location, and metadata for a specific estimation record. |
| `GET` | `/estimations/download/{estimation_id}/` | `200 OK` | Download the serialized `safetensors` archive as `application/octet-stream`. |
| `DELETE` | `/estimations/{estimation_id}/` | `204 No Content` | Delete the estimation record, all associated visualization outputs, and their corresponding object storage artifacts. |

### Visualization Jobs — `/visualizations`

Manages the submission and retrieval of annotated video rendering tasks.

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/visualizations/submit/` | `202 Accepted` | Submit an annotated video rendering task. Validates the source estimation record and enqueues the rendering pipeline. Returns a `TaskResponse` for polling. Deduplication and storage key generation are performed within the worker. |
| `GET` | `/visualizations/` | `200 OK` | Retrieve a paginated list of visualization records ordered by primary key. Supports `skip` and `limit` query parameters. |
| `GET` | `/visualizations/{visualization_id}/` | `200 OK` | Retrieve overlay configuration, encoding parameters, and storage location for a specific visualization record. |
| `GET` | `/visualizations/download/{visualization_id}/` | `200 OK` | Download the rendered MP4 file as `application/octet-stream`. |
| `DELETE` | `/visualizations/{visualization_id}/` | `204 No Content` | Delete the visualization record and its corresponding object storage artifact. |

### Task Polling — `/tasks`

Provides a unified interface for tracking the asynchronous execution state of any submitted job (estimation or visualization).

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `GET` | `/tasks/{task_id}/` | `200 OK` | Poll the current execution state and result payload of a submitted task. Valid status values strictly align with the Orchestration Model state machine: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`. The `result` field is populated only when `status` is `COMPLETED`. |

## Schema and Validation

> **Note:**  
> The full request and response schemas, field-level validation constraints, and exact error codes for all endpoints are available via the auto-generated OpenAPI specification. To export it, refer to [the corresponding script](../scripts/utils/export_swagger.py).

## Next Steps

With the architectural boundaries, data models, and external API contracts formally defined, the remaining task is to document how the system executes at runtime and how it is deployed.

The previous sections covered the conceptual design, the concurrency models, the domain schemas, the engineering decisions, and the HTTP interface. The remaining documentation shifts focus from abstract architectural design to concrete operational details:

1. **Request flows** — sequence diagrams tracing inter-component communication, content-addressed deduplication, and the asynchronous Submit-and-Poll lifecycle.
2. **Codebase layout** — repository structure, module boundaries, and the organization of the service layer and worker processes.
3. **Dependencies and infrastructure** — the concrete technology stack, mapping architectural roles to specific Python frameworks, message brokers, and storage backends.
4. **Deployment and usage** — environment setup via containerization, infrastructure provisioning, and minimal examples of service invocation.

These sections define the exact runtime behavior of the service and provide the operational blueprint required for local development, production deployment, and ongoing maintenance.