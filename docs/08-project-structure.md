# VIII. **Project Structure**

> *This document describes the logical organization of the project codebase, covering the application source layout and supporting configuration, infrastructure, and tooling directories.*

## Directory Layout

```bash
pose-estimation-service/
├── app/                            # Application source code, organized by runtime process.
│   │                               # Each top-level subdirectory corresponds to an independently
│   │                               # deployable process with its own entry point and dependencies.
│   │
│   ├── shared/                     
│   │   ├── postgres/               # SQLAlchemy models, repositories, and session management 
│   │   │                           # (implements the relational Metadata Store).
│   │   ├── minio/                  # Object storage client and presigned URL operations 
│   │   │                           # (implements the Payload Storage).
│   │   └── redis/                  # Redis client configuration (serves dual roles: 
│   │                               # ephemeral State Store for polling and Task Queue broker).
│   │
│   ├── server/                     # FastAPI application (the synchronous Service Layer).
│   │   ├── modules/                # Route handlers grouped by domain resource.
│   │   │   ├── health/             # Liveness and readiness health check endpoints.
│   │   │   ├── task/               # Task status polling endpoint (queries the State Store).
│   │   │   ├── video/              # Video ingestion, retrieval, download, and deletion.
│   │   │   ├── estimation/         # Estimation submission, retrieval, download, and deletion.
│   │   │   └── visualization/      # Visualization submission, retrieval, download, and deletion.
│   │   └── exception_handlers/     # Global HTTP and validation error handlers 
│   │                               # (ensures unified, decoupled error responses).
│   │
│   └── workers/                    # Background execution contexts.
│       ├── task_queue/             # Celery application instance and broker configuration.
│       ├── task_infra/             # Shared worker utilities: streaming frame extraction, 
│       │                           # tensor I/O, content-addressed deduplication, and schemas.
│       ├── inference/              # Inference worker: maintains a persistent 
│       │   │                       # `ensam3d_inference` pipeline instance in VRAM.
│       │   └── tasks/estimate/     # Task implementation: artifact upload and DB persistence.
│       └── default/                # Post-processing worker: CPU-bound tasks (e.g., video 
│           │                       # rendering). Isolated from inference to prevent VRAM waste.
│           └── tasks/visualize/    # Task implementation: frame rendering and video encoding.
│
├── docker/                         # Docker Compose stacks for local (infrastructure-only) and 
│                                   # deploy (fully containerized) modes.
│
├── config/                         # Environment variable templates for local and deploy modes.
│
├── migrations/                     # Alembic migration environment and database schema 
│                                   # change scripts (manages the Metadata Store evolution).
│
└── scripts/
    ├── infra/                      # Code-generation scripts for infrastructure init files.
    ├── quick_start/                # Automated startup scripts for local and deploy modes.
    └── utils/                      # Standalone utility scripts (e.g., OpenAPI schema export).
```

## Component Overview

> **Note:** all files include inline comments describing backend-specific decisions and non-obvious implementation details.

1. **`app/shared/`**

    Centralizes all infrastructure client code shared across the API server and both worker types. This module implements the concrete clients for the architectural roles defined in the Domain Model and Runtime Architecture:
    
    - **`postgres/`** — SQLAlchemy models, repositories, and session management (implements the relational **Metadata Store**)
    - **`minio/`** — Asynchronous object storage operations (implements the **Payload Storage** for binary artifacts)
    - **`redis/`** — Redis client configuration (serves dual roles as the ephemeral **State Store** for task polling and the **Task Queue** broker)
    
    Keeping this layer separate ensures that infrastructure access patterns are defined once and consumed uniformly by all processes, preventing duplication and ensuring consistent error handling across the system.

2. **`app/server/`**

    The FastAPI application serving as the synchronous **Service Layer** defined in the Runtime Architecture. Route handlers are organized by domain resource under `modules/`, with each resource directory containing subdirectories for each supported HTTP operation (e.g., `video/ingest/`, `estimation/submit/`). This structure makes the API surface navigable by resource and operation rather than by technical artifact type, aligning with the REST resource-oriented design decisions.
    
    The `exception_handlers/` subdirectory implements the unified error handling strategy, translating internal exceptions into generic, decoupled error responses as specified in the API Design.

3. **`app/workers/`**

    Contains all Celery worker definitions implementing the asynchronous execution contexts from the Runtime Architecture:
    
    - **`task_queue/`** — Holds the shared Celery application instance used by both the server (for enqueuing tasks) and workers (for execution). Configures broker connection, serialization, and task routing.
    - **`task_infra/`** — Provides utilities shared across worker types: batched frame extraction (streaming video processing), `safetensors` serialization, content-addressed deduplication logic, and shared type definitions. Centralizing these utilities prevents code duplication and ensures consistent behavior across inference and post-processing workflows.
    - **`inference/`** — The GPU-bound inference worker process. Maintains a persistent `ensam3d_inference` pipeline instance in VRAM (Stateless Logic, Stateful Process pattern). Contains task implementations for 3D pose estimation, artifact upload, and database persistence.
    - **`default/`** — The CPU-bound post-processing worker process. Isolated from inference to prevent VRAM waste on non-ML tasks. Contains task implementations for video rendering, frame compositing, and encoding.
    
    Each worker has its own entry point, configuration, and resource allocation strategy, enabling independent scaling and deployment.

4. **`config/`**

    Environment variable templates and configuration files for local development and production deployment modes. Separates configuration from code, enabling the same codebase to run in different environments without modification.

5. **`migrations/`**

    Alembic migration environment managing the evolution of the **Metadata Store** schema. Contains the configuration file (`alembic.ini`), migration script template, and all versioned migration files. Migrations are generated via `just db-revision` (creates a new migration script from model changes) and applied via `just db-migrate` (executes pending migrations against the database).
    
    This separation ensures that schema changes are version-controlled, reviewable, and can be applied consistently across environments.

6. **`docker/`**

    Dockerfiles for each deployable service (`server`, `inference` worker, `default` worker) and Docker Compose configurations for two deployment modes:
    
    - **Local development** (`docker-compose.local.yml`) — Provisions infrastructure services only (PostgreSQL, Redis, MinIO) while running application code directly on the host for rapid iteration.
    - **Production deployment** (`docker-compose.deploy.yml`) — Fully containerized stack with all services running in isolated containers.
    
    The `postgres/`, `redis/`, and `minio/` subdirectories contain initialization artifacts (SQL scripts, ACL rules, bucket policies) generated by the infrastructure scripts in `scripts/infra/`.

7. **`scripts/`**

    | Directory | Description |
    |-----------|-------------|
    | **`infra/`** | Generates infrastructure initialization artifacts from environment variables: `.env` file template, PostgreSQL user creation SQL (enforcing the Principle of Least Privilege), Redis ACL rules, and MinIO bucket policy and setup script. Ensures reproducible infrastructure provisioning across environments. |
    | **`quick_start/`** | One-command startup scripts for local development (`start-local.sh`) and full containerized deployment (`start-deploy.sh`). Orchestrate infrastructure provisioning, database migration, and process launch in the correct dependency order, eliminating manual setup steps. |
    | **`utils/`** | Developer utilities. Currently contains the OpenAPI specification export script (`export_swagger.py`) referenced in the API Design documentation. |