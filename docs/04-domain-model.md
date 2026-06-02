# IV. **Domain Model**

> *This document defines the core domain entities, their storage requirements, and concrete database schemas for the Human Pose Estimation Service.*

## Overview

The Orchestration Model, defined in the previous document, serves as the ephemeral **control plane** of the system. It tracks job lifecycles, routes tasks to workers, and discards its state once a job reaches a terminal state. However, the actual business value of the Human Pose Estimation Service — the input videos, the computed 3D meshes, and the rendered visualizations — must be durably persisted.

The Domain Model serves as the system's **data plane**. It defines the core business entities and their persistence strategies. A fundamental characteristic of these entities is their dual nature: they consist of lightweight, highly structured **metadata** (used for querying, filtering, and relational integrity) and heavy, unstructured **binary artifacts** (the actual video frames and tensor data). 

This strict separation between metadata and artifacts dictates a bifurcated storage architecture, where each storage technology is selected based on its specific access patterns and scalability characteristics.

## Domain Entities

The service operates on three primary domain entities, representing a strict linear progression through the data lifecycle:

| Entity | Role in Lifecycle | Metadata Focus | Binary Artifact |
|--------|-------------------|----------------|-----------------|
| **Video** | Input ingestion | Upload parameters, spatial/temporal dimensions, client ownership | Sequence of RGB frames encoded as a video container |
| **Estimation** | Inference output | Processing parameters, sampling rates, validity flags | Serialized 3D keypoints, mesh vertices, and camera parameters |
| **Visualization** | Output rendering | Rendering configuration, overlay toggles, encoding quality | Annotated video file with geometric overlays |

## Storage Architecture Decisions

The dual nature of the domain entities creates two distinct storage concerns that must be addressed independently. Storing heavy binary artifacts in a relational database bloats the engine and destroys query performance, while storing highly relational metadata in an object store forces the application layer to manually enforce referential integrity.

To resolve this, the system employs a polyglot persistence strategy. The following table formalizes the architectural decisions for each storage concern.

| Decision | Rationale | Why Not Alternatives? |
|----------|-----------|-----------------------|
| **Relational Database (SQL) for Metadata** | Domain entities have well-defined, stable structures and strict hierarchical relationships (a `Visualization` requires an `Estimation`, which requires a `Video`). A relational database enforces referential integrity via foreign keys, supports cascading deletes, and provides ACID transactions. This ensures that an estimation record can never exist without its source video, preventing orphaned metadata. | **NoSQL / Document Stores (e.g., MongoDB)**: Lack native joins and strict referential integrity. Enforcing relational constraints at the application layer introduces race conditions and orphaned records during concurrent failures. <br><br> **Key-Value Stores (e.g., Redis)**: Optimized for ephemeral caching, not durable, complex relational querying across multiple entity types. |
| **Object Storage (S3-compatible) for Artifacts** | Binary artifacts (videos, tensor archives) are large, immutable after creation, and accessed via HTTP. Object storage provides virtually unlimited horizontal scalability, native HTTP retrieval, and built-in CDN integration. It completely decouples storage capacity from the compute nodes running the inference workers. | **Local Filesystem / NFS**: Ties binary state to specific compute nodes. If an inference worker crashes or is replaced, its local artifacts are lost or inaccessible to other nodes. NFS introduces severe network bottlenecks and locking issues under high concurrency. <br><br> **Database BLOBs**: Storing multi-megabyte videos in SQL rows bloats the database, ruins index performance, and makes backups prohibitively expensive and slow. |
| **`safetensors` for Estimation Serialization** | The `Estimation` artifact contains dense `float32` tensors (mesh vertices, keypoints). `safetensors` provides zero-copy memory mapping, native PyTorch integration, and strict safety guarantees. | **Pickle**: Poses a severe arbitrary code execution security risk during deserialization and is fragile to class definition changes. <br><br> **JSON / Protobuf**: Extremely verbose and inefficient for dense, multi-dimensional floating-point arrays, leading to massive storage and network overhead. |

## Entity Schemas

The following sections define the concrete metadata schema for each domain entity. These fields are persisted as rows in the relational database. 

Crucially, the database **never stores the binary data directly**. Instead, each record contains a `storage_key` field, which serves as an explicit, immutable pointer to the corresponding binary artifact in the Object Storage.

### `Video`

Represents an uploaded video asset and serves as the root entity from which all downstream processing originates. 

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Primary key. Auto-incrementing surrogate identifier. |
| `storage_key` | `str` | Immutable object storage path to the raw video file. |
| `width` | `int` | Frame width in pixels. |
| `height` | `int` | Frame height in pixels. |
| `fps` | `float` | Nominal frame rate of the video source. |
| `duration_seconds` | `float` | Total playback duration in seconds. |
| `description` | `str \| None` | Optional human-readable label for operational identification. |
| `created_at` | `datetime` | Timezone-aware creation timestamp in UTC. |

> **Lifecycle Rule:** The `Video` entity is the root of the relational graph. Deleting a `Video` record triggers a cascading delete across all dependent `Estimation` and `Visualization` records in the database, and issues asynchronous deletion requests to the Object Storage for their corresponding binary artifacts.

### `Estimation`

Represents a completed 3D pose estimation run over a specific temporal and spatial window of a source video. 

The client controls the inference workload via preprocessing parameters: `skip_start_seconds` and `duration_seconds` define the temporal window, `requested_fps` controls temporal downsampling, and `requested_width` / `requested_height` define the spatial resolution fed into the `ensam3d_inference` pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Primary key. |
| `video_id` | `int` | Foreign key referencing the source `Video` record. |
| `storage_key` | `str` | Immutable object storage path to the serialized `safetensors` archive. |
| `requested_width` | `int` | Target frame width in pixels applied during preprocessing. |
| `requested_height` | `int` | Target frame height in pixels applied during preprocessing. |
| `requested_fps` | `float` | Frame sampling rate applied before inference. |
| `skip_start_seconds` | `float` | Temporal offset in seconds skipped from the video start. |
| `duration_seconds` | `float` | Total analyzed segment duration in seconds. |
| `description` | `str \| None` | Optional human-readable label. |
| `created_at` | `datetime` | Timezone-aware creation timestamp in UTC. |

### `Visualization`

Represents a rendered, annotated video derived from a completed estimation. This entity is generated post-inference to provide visual validation of the model's predictions.

The client controls the rendering pipeline via boolean overlay toggles (`show_*`) and the video encoding trade-offs via `crf` (quality vs. size) and `preset` (CPU time vs. compression efficiency).

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Primary key. |
| `estimation_id` | `int` | Foreign key referencing the source `Estimation` record. |
| `storage_key` | `str` | Immutable object storage path to the rendered MP4 file. |
| `show_bbox` | `bool` | Whether bounding boxes were rendered in the output video. |
| `show_bbox_confidence` | `bool` | Whether detection confidence scores were rendered. |
| `show_keypoints` | `bool` | Whether 2D keypoint markers were overlaid. |
| `show_skeleton` | `bool` | Whether skeletal connections between keypoints were drawn. |
| `crf` | `int` | x264 Constant Rate Factor (0-51). Lower values yield higher quality and larger file sizes. |
| `preset` | `str` | x264 encoding preset (`ultrafast` to `veryslow`). Controls the CPU time vs. compression efficiency trade-off. |
| `description` | `str \| None` | Optional human-readable label. |
| `created_at` | `datetime` | Timezone-aware creation timestamp in UTC. |

## Next Steps

With the domain entities, relational schemas, and polyglot storage strategies formally defined, the Domain Model is complete. The system now possesses a robust **data plane** capable of durably persisting the hierarchical relationships between `Video`, `Estimation`, and `Visualization` metadata, while safely offloading heavy binary artifacts to scalable object storage.

However, a static data model only describes *where* and *how* data is stored; it does not define the operational policies governing *how* data enters, moves through, and is protected within the system. Before we can design the concrete HTTP API endpoints that clients will use to interact with these entities, we must first establish the foundational engineering constraints and architectural policies that dictate the system's runtime behavior.

Several critical operational questions remain unanswered at the API boundary:
- **Ingestion & Validation:** How does the system neutralize malformed or malicious video payloads before they reach the inference workers or exhaust storage capacity? Should clients upload directly to object storage, or must the service layer intercept the payload?
- **Resource Optimization:** How does the system prevent redundant computation and storage costs when clients submit identical videos or request the exact same estimation parameters?
- **Hardware Topology:** Given that `Estimation` (GPU-bound, heavy VRAM footprint) and `Visualization` (CPU-bound, encoding-intensive) have radically different resource profiles, how should the worker topology be structured to maximize hardware utilization without wasting VRAM on rendering tasks?
- **Security & Parity:** How do infrastructure credentials and environment configurations scale securely from local development to production deployments?

These concerns transcend the Domain Model and belong to the operational architecture of the service layer. The next document addresses these exact challenges, formalizing the **Engineering Decisions** that define the system's ingestion pipelines, resource isolation strategies, and security boundaries. These decisions will, in turn, serve as the strict prerequisites for designing the external API contract.