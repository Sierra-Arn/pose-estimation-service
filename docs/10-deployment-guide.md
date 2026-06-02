# X. **Deployment Guide**

> *This document describes the step-by-step deployment process for both launch modes, with a detailed breakdown of what each step does and why it is required.*

## Overview

The service supports two launch modes:

- **Local mode** — infrastructure services (PostgreSQL, Redis, MinIO) run as Docker containers; the API server and workers run directly on the host machine. Intended for development and debugging.
- **Deploy mode** — the full stack runs in Docker, including infrastructure, database migration, API server, and both worker processes. Intended for self-hosted production deployment.

Both modes are automated by a single script each. The sections below document the sequence of steps executed by each script.

### Prerequisites

- [Pixi](https://pixi.sh/latest/) package manager.
- [Docker and Docker Compose](https://docs.docker.com/engine/install/).
- GNU/Linux-based system on `x86_64` architecture.
- NVIDIA GPU with driver compatible with CUDA Toolkit `>= 12.8`.

> **Note:**  
> These prerequisites are not strict requirements but describe the environment used for development. The service can be set up in alternative environments with different package managers, operating systems, or GPU configurations if needed.

### Setup

1. **Clone the repository**

    ```bash
    git clone git@github.com:Sierra-Arn/pose-estimation-service.git
    cd pose-estimation-service
    ```

2. **Install dependencies**

    ```bash
    pixi install
    ```

3. **Activate environment**

    ```bash
    pixi shell
    ```

### Model Weights Access

The service requires the `sam-3d-body-vith` model weights, which are hosted on Hugging Face under restricted access.

1. **Request access**

    Navigate to the model repository and submit an access request:

    ```
    https://huggingface.co/facebook/sam-3d-body-vith
    ```

2. **Download weights**

    After access is granted, download the weights manually and place them in the project root:

    ```bash
    # Expected structure after download:
    pose-estimation-service/
    ├── app/
    ├── docker/
    ├── config/
    ├── migrations/
    ├── scripts/
    ├── pixi.toml
    ├── pixi.lock
    ├── justfile
    └── sam-3d-body-vith/
    ```

## **Local Mode**

Launches the infrastructure stack in Docker and starts the API server and both workers as separate terminal processes on the host.

```bash
just quick-start-local
```

**Execution sequence:**

| Step | Command | Description |
|------|---------|-------------|
| 1 | `just gen-env` | Copies `config/.env.local.example` to `.env` in the project root and generates cryptographically secure random passwords for all credential fields. Skipped if `.env` already exists. |
| 2 | `just gen-acl` | Generates `docker/redis/init/01-create-users.acl` from environment variables. Defines Redis users with scoped permissions for the application. |
| 3 | `just gen-sql` | Generates `docker/postgres/init/01-create-user.sql` from environment variables. Creates the application database user with the minimum required privileges. |
| 4 | `just gen-minio` | Generates `docker/minio/init/policy.json` and `docker/minio/init/setup.sh` from environment variables. Defines the bucket access policy and the MinIO initialization script that runs inside the init container. |
| 5 | `just docker-local-up` | Starts the infrastructure-only Docker Compose stack (`compose.local.yml`): PostgreSQL, Redis, and MinIO. |
| 6 | *(10s pause)* | Waits for infrastructure containers to become healthy before proceeding. |
| 7 | `just db-migrate` | Applies all pending Alembic migrations to bring the database schema to the current version. |
| 8 | `just server` | Launches the FastAPI/Uvicorn API server in a new terminal window. |
| 9 | `just worker-default` | Launches the default Celery worker (post-processing tasks) in a new terminal window. |
| 10 | `just worker-inference` | Launches the inference Celery worker (GPU-accelerated pose estimation tasks) in a new terminal window. |
| 11 | *(health polling)* | Polls `GET /health/shallow/` until the server responds with HTTP 200 or the retry limit is reached.  |
| 12 | *(Swagger UI opening)* | On successful health check, automatically opens the Swagger UI in the default browser. If the server fails to respond in time, prints a warning with the manual URL. |

**Cleanup:**

```bash
just docker-local-down
```

Stops the infrastructure containers and removes anonymous volumes. The API server and worker processes must be terminated manually by closing their terminal windows.

## Deploy Mode

Launches the full stack in Docker, including infrastructure, database migrations, API server, and both worker processes. Intended for self-hosted production deployment or end-to-end containerized testing.

```bash
just quick-start-deploy
```

**Execution sequence:**

| Step | Command / Action | Description |
|------|------------------|-------------|
| 1 | `just gen-env deploy` | Copies `config/.env.deploy.example` to `.env` in the project root and generates cryptographically secure random passwords for all credential fields. Skipped if `.env` already exists. |
| 2 | `just gen-acl` | Generates `docker/redis/init/01-create-users.acl` from environment variables. Defines Redis users with scoped permissions for the application. |
| 3 | `just gen-sql` | Generates `docker/postgres/init/01-create-user.sql` from environment variables. Creates the application database user with the minimum required privileges. |
| 4 | `just gen-minio` | Generates `docker/minio/init/policy.json` and `docker/minio/init/setup.sh` from environment variables. Defines the bucket access policy and the MinIO initialization script that runs inside the init container. |
| 5 | `just docker-deploy-up` | Builds all service images and starts the fully containerized Docker Compose stack (`compose.deploy.yml`): infrastructure (PostgreSQL, Redis, MinIO), database migration container, API server, default worker, and inference worker. |
| 6 | *(health polling)* | The startup script polls `GET /health/shallow/` (using the external port defined in `.env`) until the API server responds with HTTP 200 or the retry limit (20 attempts, 10s interval) is reached. |
| 7 | *(Swagger UI opening)* | On successful health check, automatically opens the Swagger UI in the default browser. If the server fails to respond in time, prints a warning with the manual URL. |

**Cleanup:**

```bash
just docker-deploy-down
```

Stops and removes all containers, networks, and build artifacts created by the deploy stack. Unlike local mode, all processes are fully containerized, so no manual terminal cleanup is required.