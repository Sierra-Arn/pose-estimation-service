# IX. **Project Structure**

> *This document describes the logical organization of the project codebase as a Python monorepo. Each package strictly follows the standard `src/` layout for clean imports, independent versioning, and reproducible builds via Pixi.*

## Repository Layout

```bash
pose-estimation-service/
├── packages/                     # Monorepo root containing all independently deployable Python modules and
│   │                             # shared libraries. Each package strictly follows the standard `src/` layout
│   │                             # (e.g., `packages/server/src/server/`) for clean imports and packaging.
│   │
│   ├── server/                   # FastAPI application handling HTTP routing, request validation,
│   │                             # database interactions, and decoupled task delegation to workers.
│   │
│   ├── worker-inference/         # Dedicated GPU worker process executing heavy ML inference
│   │                             # via the `ensam3d_inference` engine.
│   │
│   ├── worker-default/           # General-purpose CPU worker process executing background post-processing pipelines
│   │                             # (currently: rendering annotated video overlays and persisting media assets to S3).
│   │
│   ├── shared/                   # Cross-process shared infrastructure. Contains base configurations,
│   │                             # unified client abstractions for external services
│   │                             # (e.g., PostgreSQL, Redis, MinIO/S3), and more.
│   │
│   ├── scripts/                  # Standalone automation scripts for environment bootstrapping,
│   │                             # infrastructure initialization, and auxiliary utility tasks 
│   │                             # (e.g., OpenAPI schema export).
│   │
│   └── benchmarks/               # Performance testing suite for measuring endpoint latency,
│                                 # pipeline throughput, and parallel processing efficiency.
│
├── docker/                       # Docker Compose stacks for local (infrastructure-only) and 
│                                 # deploy (fully containerized) modes.
│
├── config/                       # Environment variable templates for local and deploy modes.
│
└── migrations/                   # Alembic migration environment and database schema change scripts.
```

## Package Overview

> **Note:** all files include inline comments describing backend-specific decisions and non-obvious implementation details.

### 1. `packages/server/`

The FastAPI application serving as the synchronous **Service Layer** defined in the Runtime Architecture. This package implements the HTTP boundary of the system, handling request validation, response serialization, and task delegation to background workers.

```bash
server/
├── pyproject.toml
└── src/server/
    ├── app.py                    # FastAPI application factory and middleware configuration.
    ├── config.py                 # Environment-based settings (Pydantic BaseSettings).
    ├── main.py                   # Uvicorn entry point for the ASGI server.
    ├── logger.py                 # Structured logging configuration.
    ├── exception_handlers/       # Global HTTP and validation error handlers 
    │                             # (ensures unified, decoupled error responses).
    └── modules/                  # Route handlers grouped by domain resource.
        ├── health/               # Liveness and readiness health check endpoints.
        │   ├── shallow/          # Shallow health check (API process only).
        │   └── deep/             # Deep health check (infrastructure connectivity).
        ├── task/                 # Task status polling endpoint (queries the State Store).
        ├── video/                # Video ingestion, retrieval, download, and deletion.
        │   ├── ingest/           # POST endpoint for video upload and validation.
        │   ├── get/              # GET endpoint for video metadata retrieval.
        │   ├── download/         # GET endpoint for presigned URL generation.
        │   └── delete/           # DELETE endpoint for video removal.
        ├── estimation/           # Estimation submission, retrieval, download, and deletion.
        │   ├── submit/           # POST endpoint for estimation task submission.
        │   ├── get/              # GET endpoint for estimation metadata retrieval.
        │   ├── download/         # GET endpoint for safetensors download.
        │   └── delete/           # DELETE endpoint for estimation removal.
        └── visualization/        # Visualization submission, retrieval, download, and deletion.
            ├── submit/           # POST endpoint for visualization task submission.
            ├── get/              # GET endpoint for visualization metadata retrieval.
            ├── download/         # GET endpoint for rendered MP4 download.
            └── delete/           # DELETE endpoint for visualization removal.
```

Route handlers are organized by domain resource under `modules/`, with each resource directory containing subdirectories for each supported HTTP operation. This structure makes the API surface navigable by resource and operation rather than by technical artifact type, aligning with the REST resource-oriented design decisions.

The `exception_handlers/` subdirectory implements the unified error handling strategy, translating internal exceptions into generic, decoupled error responses as specified in the API Design.

### 2. `packages/worker-inference/`

The GPU-bound inference worker process implementing the asynchronous execution context for 3D human pose estimation. This worker maintains a persistent `ensam3d_inference` pipeline instance in VRAM, following the Stateless Logic, Stateful Process pattern.

```bash
worker-inference/
├── pyproject.toml
└── src/worker_inference/
    ├── config.py                 # Worker-specific configuration (model paths, batch sizes).
    ├── main.py                   # Celery worker entry point with GPU initialization.
    ├── _state.py                 # Global pipeline instance management (loaded once at startup).
    └── tasks/
        └── estimate/             # Task implementation for 3D pose estimation.
            ├── metadata_persistor.py  # Saves estimation metadata to PostgreSQL.
            └── output_uploader.py     # Uploads safetensors to MinIO.
```

This worker is isolated from post-processing tasks to prevent VRAM waste on non-ML operations. The `_state.py` module ensures that the heavy model weights are loaded exactly once when the worker process starts, not on every task invocation.

### 3. `packages/worker-default/`

The CPU-bound post-processing worker process executing background tasks that do not require GPU acceleration. Currently, this worker handles video visualization rendering and encoding.

```bash
worker-default/
├── pyproject.toml
└── src/worker_default/
    ├── config.py                 # Worker-specific configuration (FFmpeg settings).
    ├── main.py                   # Celery worker entry point.
    └── tasks/
        └── visualize/            # Task implementation for video rendering.
            ├── render.py         # Frame compositing and overlay generation.
            ├── viz_uploader.py   # Uploads rendered MP4 to MinIO.
            └── config.py         # Visualization-specific parameters.
```

This worker uses a `prefork` pool with `concurrency=4`, allowing multiple CPU-bound rendering tasks to execute in parallel. It is completely isolated from the inference worker to ensure that GPU memory remains dedicated to ML workloads.

### 4. `packages/shared/`

Centralizes all infrastructure client code and shared utilities consumed by the API server and both worker types. This package implements the concrete clients for the architectural roles defined in the Domain Model and Runtime Architecture.

```bash
shared/
├── pyproject.toml
└── src/
    ├── base_lib/                 # Foundational utilities shared across all packages.
    │   ├── base_config.py        # Base configuration class with environment variable loading.
    │   └── logger.py             # Structured logging setup.
    │
    ├── postgres_lib/             # Relational database layer (implements Metadata Store).
    │   ├── config.py             # PostgreSQL connection settings.
    │   ├── session.py            # SQLAlchemy async session factory.
    │   ├── models/               # ORM models for domain entities.
    │   │   ├── video.py          # Video metadata model.
    │   │   ├── estimation.py     # Estimation metadata model.
    │   │   └── visualization.py  # Visualization metadata model.
    │   └── repositories/         # Data access layer (Repository pattern).
    │       ├── video.py          # Video CRUD operations.
    │       ├── estimation.py     # Estimation CRUD operations.
    │       └── visualization.py  # Visualization CRUD operations.
    │
    ├── minio_lib/                # Object storage layer (implements Payload Storage).
    │   ├── config.py             # MinIO connection settings.
    │   ├── operations.py         # Upload, download, presigned URL generation.
    │   └── utils.py              # Bucket and object key utilities.
    │
    ├── redis_lib/                # In-memory store client (implements State Store).
    │   └── config.py             # Redis connection settings.
    │
    └── task_queue/               # Celery task queue infrastructure.
        ├── config.py             # Celery broker and result backend settings.
        ├── instance.py           # Celery application factory.
        └── infrastructure/       # Shared worker utilities.
            ├── frame_extractor.py    # Streaming video frame extraction.
            ├── tensors_io.py         # Safetensors serialization/deserialization.
            ├── validator.py          # Content validation utilities.
            └── types.py              # Shared type definitions.
```

Keeping this layer separate ensures that infrastructure access patterns are defined once and consumed uniformly by all processes, preventing duplication and ensuring consistent error handling across the system.

### 5. `packages/scripts/`

Standalone automation scripts for environment bootstrapping, infrastructure initialization, and developer utilities. These scripts are not part of the runtime application but are essential for development workflow and deployment.

```bash
scripts/
├── pyproject.toml
└── src/scripts/
    ├── quick_start/              # Automated startup scripts.
    │   ├── shared.py             # Common utilities (API URL construction, health checks).
    │   ├── local.py              # Local development mode launcher.
    │   └── deploy.py             # Full containerized deployment launcher.
    └── utils/                    # Developer utilities.
        ├── init_env.py           # Generates .env file from templates.
        ├── generate_postgres_sql.py  # Generates PostgreSQL user creation SQL.
        ├── generate_redis_acl.py     # Generates Redis ACL rules.
        ├── generate_minio_setup.py   # Generates MinIO bucket setup script.
        └── export_swagger.py         # Exports OpenAPI specification to JSON.
```

The `quick_start/` scripts orchestrate infrastructure provisioning, database migration, and process launch in the correct dependency order, eliminating manual setup steps. The `utils/` scripts generate infrastructure initialization artifacts from environment variables, enforcing the Principle of Least Privilege for database users and Redis ACLs.

### 6. `packages/benchmarks/`

Performance testing suite for measuring endpoint latency, pipeline throughput, and parallel processing efficiency. This package contains both the benchmark logic and the entry-point scripts for execution.

```bash
benchmarks/
├── pyproject.toml
└── src/benchmarks/
    ├── core/                     # Benchmark logic and shared utilities.
    │   ├── __init__.py           # Common functions (CPU/GPU detection, service management).
    │   ├── ingestion_latency.py  # Ingestion endpoint latency measurement.
    │   ├── estimation_latency.py # Estimation task latency measurement.
    │   └── parallel_pipeline.py  # End-to-end parallel pipeline benchmark.
    ├── ingestion_latency.py      # Entry point for ingestion benchmark.
    ├── estimation_latency.py     # Entry point for estimation benchmark.
    └── parallel_pipeline.py      # Entry point for parallel pipeline benchmark.
```

Each benchmark script automatically provisions infrastructure, starts the necessary services, executes the test, and reports results with detailed configuration metadata. The `core/` module contains reusable async functions for HTTP requests, task polling, and result aggregation.

## Infrastructure Directories

### 7. `config/`

Environment variable templates for local development and production deployment modes. Separates configuration from code, enabling the same codebase to run in different environments without modification.

### 8. `migrations/`

Alembic migration environment managing the evolution of the **Metadata Store** schema. Contains the configuration file (`alembic.ini`), migration script template, and all versioned migration files. Migrations are generated via `just db-revision` (creates a new migration script from model changes) and applied via `just db-migrate` (executes pending migrations against the database).

This separation ensures that schema changes are version-controlled, reviewable, and can be applied consistently across environments.

### 9. `docker/`

Dockerfiles for each deployable service and Docker Compose configurations for two deployment modes:

```bash
docker/
├── Dockerfile.server             # FastAPI application container.
├── Dockerfile.worker-inference   # GPU inference worker container.
├── Dockerfile.worker-default     # CPU post-processing worker container.
├── compose.local.yml             # Local development (infrastructure only).
├── compose.deploy.yml            # Production deployment (full stack).
├── postgres/init/                # PostgreSQL initialization scripts.
│   └── 01-create-user.sql        # Creates application database user.
├── redis/init/                   # Redis initialization scripts.
│   └── 01-create-users.acl       # Defines Redis ACL rules.
└── minio/init/                   # MinIO initialization scripts.
    ├── policy.json               # Bucket access policies.
    └── setup.sh                  # Bucket creation and policy application.
```

- **Local development** (`compose.local.yml`) — Provisions infrastructure services only (PostgreSQL, Redis, MinIO) while running application code directly on the host for rapid iteration.
- **Production deployment** (`compose.deploy.yml`) — Fully containerized stack with all services running in isolated containers.

The `postgres/`, `redis/`, and `minio/` subdirectories contain initialization artifacts generated by the infrastructure scripts in `packages/scripts/utils/`.