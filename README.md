# **Human Pose Estimation Service**  

> *Production-oriented REST API service exposing [`ensam3d_inference`](https://github.com/Sierra-Arn/ensam3d-lib/tree/main/docs/ensam3d_inference) as a managed backend for distributed 3D human pose estimation, with video ingestion, GPU worker orchestration, annotated visualization rendering, and persistent artifact storage.*

## Performance Benchmark

This benchmark demonstrates the full processing pipeline of the system running in parallel across multiple videos. Each video independently goes through three stages: 
1. *ingestion* (upload + validation), 
2. *pose estimation* (GPU inference), 
3. *visualization rendering* (video overlay generation).

The key metric is the Parallelism Ratio — the ratio between the sum of all individual stage latencies and the actual wall-clock time. In this benchmark, a ratio of 6.36x demonstrates that the distributed architecture completed the entire workload 6.36 times faster than a single sequential pipeline would have.

### Benchmark Videos

All videos were sourced from [Pexels](https://www.pexels.com/) and processed simultaneously:

| # | Video | Resolution | Duration | Size |
|---|-------|------------|----------|------|
| 1 | [Person jogging at the beach](https://www.pexels.com/video/person-jogging-at-the-beach-4928018/) | 1920 × 1080 | 8.93 sec | 5.69 MB |
| 2 | [Man with prosthetic leg jogging](https://www.pexels.com/video/man-with-prosthetic-leg-jogging-8344814/) | 3840 × 2160 | 24.32 sec | 72.10 MB |
| 3 | [A man running on the beach shore](https://www.pexels.com/video/a-man-running-on-the-beach-shore-3125907/) | 3840 × 2160 | 12.60 sec | 28.55 MB |
| 4 | [A man jogging by the lakeside](https://www.pexels.com/video/a-man-jogging-by-the-lakeside-3209300/) | 3840 × 2160 | 15.36 sec | 22.63 MB |
| 5 | [A man running at the beach](https://www.pexels.com/video/a-man-running-at-the-beach-9184994/) | 3840 × 2160 | 26.10 sec | 77.51 MB |
| 6 | [A woman running in the beach](https://www.pexels.com/video/a-woman-running-in-the-beach-3191808/) | 3840 × 2160 | 16.48 sec | 48.59 MB |
| 7 | [A person running on the beach at sunset](https://www.pexels.com/video/a-person-running-on-the-beach-at-sunset-4443743/) | 1920 × 1080 | 12.96 sec | 7.74 MB |
| 8 | [Woman jogging by the seashore](https://www.pexels.com/video/woman-jogging-by-the-seashore-3192083/) | 3840 × 2160 | 14.84 sec | 41.02 MB |
| 9 | [A man running on the beach](https://www.pexels.com/video/a-man-running-on-the-beach-5968011/) | 1280 × 720 | 9.97 sec | 3.27 MB |
| 10 | [Man jogging outdoors](https://www.pexels.com/video/man-jogging-outdoors-6022795/) | 3840 × 2160 | 15.64 sec | 46.78 MB |

### Configuration

**Environment**

| | |
|-----------------------------|-------------------------------------------------------------|
| CPU                         | AMD Ryzen 7 5800H with Radeon Graphics                      |
| GPU                         | NVIDIA GeForce RTX 3070 Laptop GPU                          |
| PyTorch Version             | 2.5.1.post306                                               |
| CUDA Version                | 12.6                                                        |
| Number of Servers           | 1                                                           |
| Number of Default Workers   | 1 (prefork pool, CPU, concurrency 4, prefetch_multiplier 1) |
| Number of Inference Workers | 2 (solo pool, CUDA, concurrency 1, prefetch_multiplier 1)   |

**Estimation Parameters**

| | |
|-------------------------|-------------|
| Target Resolution       | 1920 × 1080 |
| Target Duration         | 10.00 sec   |
| Target FPS              | 20.00       |
| Target Frames per Video | 200         |
| Inference Batch Size    | 30          |

**Visualization Parameters**

| | |
|--------------------------|--------|
| Show Keypoints           | True   |
| Show Skeleton            | True   |
| Show Bounding Boxes      | False  |
| CRF (Quality)            | 20     |
| Encoding Preset          | medium |
| Visualization Batch Size | 30     |

### Performance

| | |
|------------------------|------------|
| Total Videos Processed | 10         |
| Wall-Clock Time        | 135.68 sec |
| Summed Stage Times     | 863.15 sec |
| Parallelism Ratio      | 6.36x      |

> **Want more details?**  
> For the full technical documentation — including conceptual design, domain modeling, runtime concurrency, API contracts, deployment guides, and more — see [the documentation](./docs/README.md).

## Project Structure

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
├── migrations/                   # Alembic migration environment and database schema change scripts.
│
├── docs/                         # Technical documentation covering conceptual overview,
│                                 # domain model, runtime architecture, engineering decisions,
│                                 # API design, codebase layout, and dependencies.
│
├── pixi.toml                     # Pixi environment configuration defining feature-based
│                                 # dependency groups for server, workers, and ML inference.
│
├── pixi.lock                     # Fully resolved and reproducible dependency lockfile.
│
└── justfile                      # Task runner: bootstrap commands, database migration targets,
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