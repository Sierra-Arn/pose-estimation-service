# **Human Pose Estimation Service**  

*FastAPI service that detects poses in videos (YOLO + Sapiens), computes joint angles, performs running biomechanical analysis [^1], and integrates with MinIO for storage.*

[^1]: Current implementation includes time-averaged joint angles across the entire video and min/max values for arm swing amplitude.

## **Project Structure**

```bash
pose-estimation-service/
├── app/
│   ├── human_pose_estimator/   # Core pose estimation pipeline: human detection (YOLO), 
│   │                           # pose estimation (Sapiens), keypoint processing
│   ├── s3/                     # S3 client and service layer for interacting with MinIO storage
│   ├── video/                  # Video I/O, rendering, skeleton overlay, and frame processing utilities
│   ├── running_analysis/       # Higher-level biomechanical analysis
│   ├── pickle_data/            # Serialization logic for input/output data structures
│   ├── rest/                   # FastAPI application: ML and storage endpoints, request schemas, and API routing
│   └── shared/                 # Shared configuration and base classes used across modules
├── docs/                       # Architecture and design documentation: diagrams illustrating 
│                               # user flows, data flows, component interactions
├── docker-compose.yml          # Docker Compose file for launching MinIO 
├── .env.example                # Example environment variables file
├── justfile                    # Project-specific commands using Just
├── pixi.lock                   # Locked dependency versions for reproducible environments
├── pixi.toml                   # Pixi project configuration: environments, dependencies, 
|                               # platforms and environment-specific commands
└── playground-testing/         # Jupyter notebooks for step-by-step validation 
                                # of the full pose estimation pipeline logic
```

## **Dependencies Overview**

- [pydantic-settings](https://github.com/pydantic/pydantic-settings) — 
a Pydantic-powered library for managing application configuration and environment variables with strong typing, validation, and seamless `.env` support.

- [fastapi](https://github.com/fastapi/fastapi) + [uvicorn](https://github.com/Kludex/uvicorn) — 
the modern, async-ready [^2] web stack used to expose the pose estimation pipeline via a clean, well-documented REST API with automatic OpenAPI/Swagger support.

[^2]: Even though the entire inference pipeline is synchronous, I deliberately chose FastAPI + Uvicorn because I lack experience with traditional synchronous frameworks like Flask or Django REST.

- [opencv](https://github.com/opencv/opencv) + [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) — 
core media processing tools for efficient video encoding, decoding, and rendering of annotated outputs.

- [boto3](https://github.com/boto/boto3) — 
the official AWS SDK for Python, used here to interact with S3-compatible storage (MinIO) for video uploads, analysis artifacts, and metadata persistence.

- [just](https://github.com/casey/just) —
a lightweight, cross-platform command runner that replaces complex shell scripts with clean, readable, and reusable project-specific recipes. [^3]

[^3]: Despite using `pixi`, there are issues with `pixi tasks` regarding environment variable handling from `.env` files and caching mechanism that is unclear and causes numerous errors. In contrast, `just` provides predictable, transparent execution without the complications encountered with `pixi tasks` system. I truly hope `pixi tasks` have been improved by the time you’re reading this! <33

- [cuda-toolkit](https://developer.nvidia.com/cuda/toolkit) — 
the official NVIDIA toolkit that provides the CUDA runtime, compiler, and supporting libraries required to run and compile GPU-accelerated code. This dependency is only required in GPU-enabled environments and is activated exclusively when installing the `gpu` feature profile (see `pixi.toml`).

- [pytorch](https://github.com/pytorch/pytorch) + [torchvision](https://github.com/pytorch/vision) + [ultralytics](https://github.com/ultralytics/ultralytics) — 
the core deep learning stack powering human detection and pose estimation. **PyTorch** provides the tensor computation and automatic differentiation backbone; **torchvision** supplies pre-trained models and vision utilities; and **Ultralytics** delivers the YOLO-based human detector (`yolov11n.pt`) used as the first stage of the pipeline. This trio is available in two mutually exclusive configurations:
    - **GPU mode**: leverages `pytorch-gpu` and CUDA 12.8 for accelerated inference (enabled via the `gpu` feature in `pixi.toml`).
    - **CPU mode**: uses lightweight `pytorch-cpu` builds for environments without NVIDIA GPUs (enabled via the `cpu` feature).

### **Testing & Development Dependencies**

- [ipykernel](https://github.com/ipython/ipykernel) — 
the IPython kernel for Jupyter, enabling interactive notebook development and seamless integration with the project’s virtual environments.

## **Quick Start**

### **I. Prerequisites**

- [Docker and Docker Compose](https://docs.docker.com/engine/install/) container tools.
- [Pixi](https://pixi.sh/latest/) package manager.

> **Platform note**: All development and testing were performed on `linux-64`.  
> If you're using a different platform, you’ll need to:
> 1. Update the `platforms` list in the `pixi.toml` accordingly.
> 2. Ensure that platform-specific scripts are compatible with your operating system or replace them with equivalents.

### **II. Initial Setup**

1. **Clone the repository**

    ```bash
    git clone https://github.com/Sierra-Arn/pose-estimation-service.git
    cd pose-estimation-service
    ```

2. **Install dependencies**
    
    ```bash
    pixi install --all
    ```

3. **Setup environment configuration**
   ```bash
   pixi run just copy-env
   ```

### **III. Model Setup**

The pose estimation pipeline requires two pre-trained models:

1. **Human detector**: a YOLO model for person detection.
2. **Pose estimator**: a Sapiens model for keypoint regression.

To set them up:

1. **Download the models**

    - [YOLOv11n](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt) (or any compatible YOLO variant).

    - [Sapiens Pose Estimatiom Model Checkpoints COCO Checkpoints 0.3b](https://huggingface.co/noahcao/sapiens-pose-coco) (or any compatible Sapiens variant).

2. **Place models in the correct directory**

    ```bash
    mv yolov11n.pt app/human_pose_estimator/models/
    mv sapiens_0.3b_coco_best_coco_AP_796_torchscript.pt2 app/human_pose_estimator/models/
    ```

3. **Open `.env` and configure the following required variables**:

    ```env
    HUMAN_DETECTOR_MODEL_PATH=app/human_pose_estimator/models/yolov11n.pt

    ...

    POSE_ESTIMATOR_MODEL_PATH=app/human_pose_estimator/models/sapiens_0.3b_coco_best_coco_AP_796_torchscript.pt2
    ```

### **IV. Testing**

Once the environment is set up and models are in place, you can run and test the application using the interactive Jupyter notebook `playground-testing/5.test-rest.ipynb`. It demonstrates all core functionality — including service startup, video upload, pose estimation, biomechanical analysis, and result retrieval

## **License**

This project is licensed under the [BSD-3-Clause License](LICENSE).