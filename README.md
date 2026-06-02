# **Human Pose Estimation Service**  

> *Production-oriented REST API service exposing [`ensam3d_inference`](https://github.com/Sierra-Arn/ensam3d-lib/tree/main/docs/ensam3d_inference) as a managed backend for distributed 3D human pose estimation, with video ingestion, GPU worker orchestration, annotated visualization rendering, and persistent artifact storage.*

## Project Structure

```bash
pose-estimation-service/
├── app/                        # Application source code, organized by deployment unit.
│                               # Subdirectories correspond either to independently
│                               # deployable processes with their own entry points, or to
│                               # cross-process shared infrastructure.
│
├── docker/                     # Docker Compose stacks for local (infrastructure-only) and 
│                               # deploy (fully containerized) modes.
│
├── config/                     # Environment variable templates for local and deploy modes.
│
├── migrations/                 # Alembic migration environment and database schema change scripts.
│
├── scripts/                    # Standalone automation scripts for environment bootstrapping,
│                               # infrastructure initialization, and operational workflows.
│
├── docs/                       # Technical documentation covering conceptual overview,
│                               # domain model, runtime architecture, engineering decisions,
│                               # API design, codebase layout, dependencies, and deployment.
│
├── pixi.toml                   # Pixi environment configuration defining feature-based
│                               # dependency groups for server, workers, and ML inference.
│
├── pixi.lock                   # Fully resolved and reproducible dependency lockfile.
│
└── justfile                    # Task runner: bootstrap commands, database migration targets,
                                # runtime process launchers, and Docker Compose shortcuts.
                                # Automatically manages pixi environment context per recipe.
```

## Quick Start

### I. Prerequisites

- [Pixi](https://pixi.sh/latest/) package manager.
- [Docker and Docker Compose](https://docs.docker.com/engine/install/).
- GNU/Linux-based system on `x86_64` architecture.
- NVIDIA GPU with driver compatible with CUDA Toolkit `>= 12.8`.

> **Note:**  
> These prerequisites are not strict requirements but describe the environment used for development. The service can be set up in alternative environments with different package managers, operating systems, or GPU configurations if needed.

### II. Setup

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

### III. Model Weights Access

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

### IV. Launch

Once the environment is activated and model weights are downloaded, the service can be launched in one of two modes depending on the deployment context.

1. **Local mode** — infrastructure services run in Docker; the API server and workers run on the host machine directly.

    ```bash
    just quick-start-local
    ```

2. **Deploy mode** — the full stack runs in Docker, including infrastructure, API server, and both worker processes.

    ```bash
    just quick-start-deploy
    ```

    > **Note:**  
    > Deploy mode requires [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) to expose the GPU to the `worker-inference` container.

Whichever mode you choose, the launch script will automatically execute all necessary setup steps, start the server, and open the Swagger UI in your default web browser once the API is ready.

### V. Cleanup

When you are done, shut down the running services depending on the active launch mode.

1. **Local mode** — stop the API server and workers by terminating their terminal processes, then bring down the infrastructure containers.

    ```bash
    just docker-local-down
    ```

2. **Deploy mode** — stop and remove all containers with a single command.

    ```bash
    just docker-deploy-down
    ```

## Want more details?

For the full technical documentation — including conceptual design, domain modeling, runtime concurrency, API contracts, deployment guides, and more — see [the documentation](./docs/README.md).

## License

This project is licensed under the [Apache License, Version 2.0](LICENSE).