# V. Dependencies Overview

> *This document describes the dependencies required by the Human Pose Estimation Service: what each one is, the role it plays in the service, and why it was chosen over the alternatives.*

## System Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| Python | [python.org](https://www.python.org/) | Programming language | Primary language for all project source code. |
| Pixi | [prefix‑dev/pixi](https://github.com/prefix-dev/pixi) | Package and environment manager | 1. Resolves mixed Conda/PyPI dependency graphs into a single deterministic lockfile, producing fully reproducible environments. <br>2. Manages the project's virtual environment. |
| NVIDIA GPU | — | GPU hardware | Processor whose thousands of parallel cores let it perform the massively data-parallel tensor arithmetic (matrix multiplications) at the core of neural-network inference far more efficiently than a CPU. |
| CUDA driver | — | Host GPU driver | Low-level host driver (`libcuda`) that gives user-space access to the GPU, making accelerated computation possible at all. |
| Docker | [moby/moby](https://github.com/moby/moby) | Containerization platform | Container runtime that isolates and runs the service layer, the workers, and the infrastructure images. |
| Docker Compose | [docker/compose](https://github.com/docker/compose) | Multi-container orchestration tool | Declares containers, their networking, and startup order for the local and deploy execution modes. |

## Additional System Dependencies (deploy mode)

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| NVIDIA Container Toolkit | [NVIDIA/nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) | GPU passthrough for containers | Exposes the host GPU and its driver libraries inside Docker containers, so that containerized workers can run GPU-accelerated computation in deploy mode. |

## Docker Images

| Dependency | Repository | What it is | Role in the project |
|------------|------------|------------|---------------------|
| PostgreSQL | [docker.io/library/postgres](https://hub.docker.com/_/postgres) | Official Docker image for PostgreSQL | Runs the relational database engine in a container, serving as the SQL Database for the Domain Model. |
| Redis | [docker.io/library/redis](https://hub.docker.com/_/redis) | Official Docker image for Redis | Runs the in-memory data store in a container, serving as the message broker and result backend for the distributed task queue. |
| MinIO | [minio/minio](https://hub.docker.com/r/minio/minio) | S3-compatible object storage image | Runs Object Storage (S3) in a container for heavy binary artifacts (raw video, `safetensors` archives, rendered MP4 visualizations). |

## Pixi Dependencies

### Default Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| CPython | [python/cpython](https://github.com/python/cpython) | Python virtual machine | Executes all source code across every package. |
| python-dotenv | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable loader | Loads variables from .env files into os.environ at startup, making .env values available to the application. |
| requests | [psf/requests](https://github.com/psf/requests) | HTTP client | Probes the server's health endpoint on startup to confirm it has started successfully. |
| just | [casey/just](https://github.com/casey/just) | Command runner | Provides shorthand recipes for bootstrap commands, migration targets, process launchers, and Docker Compose shortcuts. |

### Shared Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| CPython | [python/cpython](https://github.com/python/cpython) | Python virtual machine | Executes all source code across every package. |
| Pydantic Settings | [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings) | Settings management library | Groups and validates environment variables, exposing them as reusable, strongly-typed config classes that the application references throughout. |
| boto3 | [boto/boto3](https://github.com/boto/boto3) | Official AWS SDK for Python | Synchronous interaction with S3. |
| aioboto3 | [terricain/aioboto3](https://github.com/terricain/aioboto3) | Async wrapper around [boto3](https://github.com/boto/boto3) and [aiobotocore](https://github.com/aio-libs/aiobotocore) | Asynchronous interaction with S3. |
| ffmpeg + PyAV | [ffmpeg/ffmpeg](https://github.com/ffmpeg/ffmpeg) + [PyAV-Org/PyAV](https://github.com/PyAV-Org/PyAV) | Multimedia framework for video/audio processing, plus its Pythonic bindings | PyAV probes video metadata (dimensions, duration, fps) directly from in-memory bytes; the `ffmpeg` CLI via subprocess decodes input video into rescaled, fps-adjusted RGB frames and encodes rendered frames back into H.264/MP4. |
| safetensors | [huggingface/safetensors](https://github.com/huggingface/safetensors) | Tensor serialization format | Serializes and deserializes the model output — a nested named tuple of tensors — preserving exact types and values. |
| SQLAlchemy | [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) | ORM and database toolkit | Maps Python classes to PostgreSQL tables and manages sessions for all database interactions. |
| Alembic | [sqlalchemy/alembic](https://github.com/sqlalchemy/alembic) | Database migration tool | Manages versioned schema changes via migration scripts. |
| psycopg | [psycopg/psycopg](https://github.com/psycopg/psycopg) | Sync + async PostgreSQL driver | Handles all database connections via SQLAlchemy's `postgresql+psycopg` dialect, serving both the async engine (async runtime) and the sync engine (Celery workers, Alembic migrations). |
| Celery | [celery/celery](https://github.com/celery/celery) | Distributed task queue | Orchestrates background execution of the inference and post-processing tasks across worker pools, with task routing between them. |
| redis-py | [redis/redis-py](https://github.com/redis/redis-py) | Official Redis client | Connects Celery to Redis as its message broker and result backend |

### Server Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| FastAPI | [fastapi/fastapi](https://github.com/fastapi/fastapi) | Async web framework | Provides HTTP routing, request validation, dependency injection, and automatic OpenAPI documentation. |
| Uvicorn | [encode/uvicorn](https://github.com/encode/uvicorn) | ASGI server | Serves the FastAPI application over HTTP. |
| python-json-logger | [nhairs/python-json-logger](https://github.com/nhairs/python-json-logger) | JSON log formatter | Formats all log records as structured JSON, enabling consistent machine-readable output. |
| filetype | [h2non/filetype.py](https://github.com/h2non/filetype.py) | MIME type detector | Validates uploaded video files by magic-byte signature before processing, preventing malicious or corrupted uploads. |

### Worker-Common Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| ensam3d-lib | [Sierra‑Arn/ensam3d‑lib](https://github.com/Sierra-Arn/ensam3d-lib) | First-party inference library | Provides the `ensam3d_inference` package, which performs fast, accurate pose estimation. |

### Worker-Inference Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| CUDA Toolkit | [nvidia.com](https://developer.nvidia.com/cuda/toolkit) | CUDA runtime and math libraries | User-space runtime and optimized GPU libraries through which PyTorch executes its tensor computations on the GPU instead of the CPU, where they run many times faster. |
| pytorch-gpu | [pytorch/pytorch](https://github.com/pytorch/pytorch) | Deep learning framework, CUDA built | Runtime for the `ensam3d_inference` package: tensor computation and neural-network execution on the GPU. |

### Worker-Default Dependencies

| Dependency | Repository | What it is | Role in the project |
|---|---|---|---|
| pytorch-cpu | [pytorch/pytorch](https://github.com/pytorch/pytorch) | Deep learning framework, CPU built | Lets the post-processing worker operate on the `torch.Tensor` results produced by the inference worker, without requiring a GPU. |

> **Note:** `ensam3d-lib` does not declare its own runtime dependencies, so they are provided manually here: `torchvision`, `timm`, `RoMa`, `Ultralytics`, `jaxtyping`, `OpenCV`, and `NumPy` (alongside `PyTorch`). It also needs the YOLO26 detector and SAM 3D Body model weights to run. These aren't documented further here — see the [`ensam3d_inference` dependencies documentation](https://github.com/Sierra-Arn/ensam3d-lib/blob/main/docs/ensam3d_inference/07-dependencies.md).

## Rationale for Dependency Choices

| Dependency | Rationale |
|---|---|
| Python | The de facto standard for machine learning and computer vision. Its ecosystem is far more mature than those of other languages, offering a comprehensive suite of production-ready libraries. |
| Pixi | Unlike Uv, it supports Conda packages, which are required here for fully reproducible environments. Unlike Miniconda/Micromamba, it resolves mixed Conda/PyPI dependency graphs into a single deterministic lockfile. |
| Docker <br>+ Docker Compose | 1. Unlike Podman, Docker is the de facto industry standard, and I already have substantial experience with it across past projects. Podman offers no advantage here that would justify switching to it and re-learning a new toolchain. <br>2. Unlike Kubernetes — which I haven't worked with and which would be overkill here, since industrial-scale deployment isn't a goal of this project — Docker Compose is a simple tool I'm already familiar with. |
| NVIDIA GPU <br>+ CUDA driver <br>+ CUDA Toolkit <br>+ NVIDIA Container Toolkit | The model's computations are heavy enough that GPU acceleration is effectively mandatory: while CPU inference is fully supported and functional, its runtimes are impractical for any production use. AMD ROCm was not targeted because it lacks full PyTorch feature parity and mature kernel optimization for transformer architectures, leaving CUDA as the only practical acceleration backend. The NVIDIA Container Toolkit, in turn, is NVIDIA's own official mechanism for exposing the GPU and its driver libraries inside containers — being the first-party way to use a proprietary technology, there is no reason to look for anything else. |
| CPython | The reference and de facto standard implementation of Python. The scientific stack is tightly coupled to its C-API and native extension model; alternative implementations (PyPy, GraalPy) lack full compatibility with compiled libraries and offer no practical speedup, since heavy computation already runs in optimized C/CUDA kernels. |
| just | Pixi has no native way to load `.env` files into its tasks — that needs `direnv`, activation scripts, or declaring every variable in `pixi.toml`. Hardcoding configuration into the manifest defeats the point of `.env` files, and the other two options add setup and implicit activation logic. Since each path adds complexity anyway, the transparent one wins: `just` loads `.env` files natively, needs no extra scripts or configuration, and its recipes are plain, readable shell commands with no hidden activation behavior. |
| ensam3d-lib | A first-party library I authored specifically to meet this project's requirements, which is precisely why it's used here. |
| PostgreSQL | This service has no special database requirements beyond a solid relational SQL engine, so the deciding factor is licensing: PostgreSQL ships under the permissive PostgreSQL License (BSD/MIT-style), the most liberal among the major open-source SQL databases, with no copyleft or commercial-use strings attached. |
| MinIO | A lightweight, S3-compatible object store that runs from a single container — the simplest free way to get an S3 API in local, CI, and deploy modes without depending on AWS. Its upstream repository was archived in early 2026 and is now source-only, so it is no longer a safe default for long-lived production systems; for this project, though, nothing simpler or free has replaced it, and the same `boto3`/`aioboto3` code would move to any S3-compatible backend (e.g. Garage, SeaweedFS) without changes if needed. |
| Redis | The backing store the task queue needs — serving as both Celery's message broker and result backend from a single instance. It was chosen for two reasons: prior hands-on experience with it, and the fact that this project needs no complex broker routing of the kind RabbitMQ specializes in, so Redis's simplicity is a better fit than a heavier message broker. |

The remaining dependencies aren't covered individually because the rationale is identical for each: every one is either the official tool for its task or the de facto standard in the Python ecosystem — the most widely used, best-documented, and most battle-tested option available, with no alternative worth the switch.