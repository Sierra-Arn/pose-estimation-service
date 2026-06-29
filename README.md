# Human Pose Estimation Service

> *Production-oriented REST API service exposing [`ensam3d_inference`](https://github.com/Sierra-Arn/ensam3d-lib/tree/main/docs/ensam3d_inference) as a managed backend for distributed 3D human pose estimation, with video ingestion, GPU worker orchestration, annotated visualization rendering, and persistent artifact storage.*

## Performance Benchmark

End-to-end performance under concurrent load is summarized below using a parallel-pipeline benchmark — ten videos of mixed resolution and size submitted simultaneously, each running independently through ingestion, estimation, and visualization.

**Configuration**

| | |
|------------------------------|-------------------------------------------------------------|
| Workload                     | 10 videos submitted simultaneously                          |
| Video Resolutions            | 720p – 4K                                                   |
| Video Sizes                  | 3.27 MB – 77.51 MB                                          |
| CPU                          | AMD Ryzen 7 5800H with Radeon Graphics                      |
| GPU                          | NVIDIA GeForce RTX 3070 Laptop GPU                          |
| PyTorch Version              | 2.5.1.post306                                               |
| CUDA Version                 | 12.6                                                        |
| Inference Workers            | 2 (solo pool, CUDA, concurrency 1)                          |
| Post-processing Workers      | 1 (prefork pool, CPU, concurrency 4)                        |

**Results**

| | |
|----------------------------|------------|
| Total Videos Processed     | 10         |
| Wall-Clock Time            | 135.68 sec |
| Summed Stage Times         | 863.15 sec |
| Parallelism Ratio          | 6.36x      |

> **Want more details?**  
> For the full technical documentation — including conceptual design, requirements, runtime concurrency, the domain model, per-endpoint request lifecycles, the dependency stack, project structure, and performance benchmarks — see [the documentation](./docs/README.md).

## Project Structure

```bash
pose-estimation-service/
├── packages/               # Monorepo root: all independently deployable
│   │                       # Python modules and shared libraries. Each
│   │                       # package uses the standard `src/` layout
│   │                       # (e.g. `packages/server/src/server/`).
│   │
│   ├── server/             # FastAPI app: HTTP routing, request
│   │                       # validation, database interactions, and
│   │                       # task delegation to the workers.
│   │
│   ├── worker-inference/   # Dedicated GPU worker running heavy ML
│   │                       # inference via the `ensam3d_inference` engine.
│   │
│   ├── worker-default/     # General-purpose CPU worker running background
│   │                       # post-processing pipelines (currently:
│   │                       # rendering annotated video overlays and
│   │                       # persisting media assets to S3).
│   │
│   ├── shared/             # Cross-process shared infrastructure: base
│   │                       # configs and unified client abstractions for
│   │                       # external services (PostgreSQL, Redis,
│   │                       # MinIO/S3), and more.
│   │
│   ├── scripts/            # Standalone automation scripts: environment
│   │                       # bootstrapping, infrastructure init, and
│   │                       # auxiliary tasks (e.g. OpenAPI schema export).
│   │
│   └── benchmarks/         # Performance testing suite: endpoint latency,
│                           # pipeline throughput, and parallel
│                           # processing efficiency.
│
├── docker/                 # Docker Compose stacks for local
│                           # (infrastructure-only) and deploy
│                           # (fully containerized) modes.
│
├── config/                 # Environment variable templates for local
│                           # and deploy modes.
│
├── migrations/             # Alembic migration environment and database
│                           # schema change scripts.
│
├── docs/                   # Technical documentation: conceptual overview,
│                           # domain model, runtime architecture,
│                           # engineering decisions, API design, codebase
│                           # layout, and dependencies.
│
├── pixi.toml               # Pixi configuration defining feature-based
│                           # dependency groups for server, workers, and
│                           # ML inference.
│
├── pixi.lock               # Fully resolved, reproducible dependency
│                           # lockfile.
│
└── justfile                # Task runner: bootstrap commands, database
                            # migration targets, runtime process launchers,
                            # and Docker Compose shortcuts. Automatically
                            # manages the pixi environment per recipe.
```

## Quick Start

### I. Prerequisites

- [Pixi](https://pixi.sh/latest/) package manager.
- [Docker and Docker Compose](https://docs.docker.com/engine/install/).
- GNU/Linux-based system on `x86_64` architecture.
- NVIDIA GPU with a driver that supports CUDA `>= 12.8`.

> **Note: on these prerequisites**  
> These are not strict requirements but describe the environment used for development. The package can be set up in alternative environments with different package managers, operating systems, or GPU configurations if needed.

> **Note: on CUDA versions**  
> The `>= 12.8` figure is a *driver* requirement, enforced through pixi's `system-requirements`. It was chosen because 12.8 was the default CUDA build shipped by PyTorch at the time development started (a plain `pip install torch` pulled the 12.8 build back then).

> **Note: the benchmarking and profiling scripts report**  
> `CUDA Version: 12.6`. This is expected and not a mismatch: that value comes from `torch.version.cuda`, i.e. the CUDA version the PyTorch binary was *compiled against*, which is independent of the newer CUDA toolkit resolved into the environment. CUDA minor-version compatibility lets a 12.6 build run on any 12.x driver with the same major version.

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

To perform pose estimation, the service requires the `sam-3d-body-vith` model weights, which are hosted on Hugging Face under restricted access. To obtain them:

1. Navigate to the [facebook/sam-3d-body-vith](https://huggingface.co/facebook/sam-3d-body-vith) repository.
2. Sign in with a Hugging Face account, request access to the repository, and wait for approval.
3. Once access is granted, download the weights manually and place the downloaded `sam-3d-body-vith/` directory in the project root.

    ```bash
    # Expected structure after download:
    pose-estimation-service/
    ├── packages/ 
    ├── docker/
    ├── config/
    ├── migrations/
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

> **Want to see what happens under the hood?**  
> The launch scripts are fully documented with step-by-step comments explaining each action. You can find them here:
> - [Local mode script](./packages/scripts/src/scripts/quick_start/local.py)
> - [Deploy mode script](./packages/scripts/src/scripts/quick_start/deploy.py)

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

## License

This project is licensed under the [Apache License, Version 2.0](LICENSE).