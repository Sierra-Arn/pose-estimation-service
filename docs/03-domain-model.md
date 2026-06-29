# III. Domain Model

> *This document defines the Domain Model of the Human Pose Estimation Service: the persistent entities it produces together with their schemas, their content-addressed storage, and the transit messages that carry work to the workers and results back.*

## Domain Entities

The Domain Model defines the system's business entities — the data the service actually produces, stores, and exchanges — as distinct from the execution machinery that moves it around. The entities fall into three groups, separated by where they live and how long they last, each following directly from a decision already made:

- **Binary payloads** — the videos and serialized results — in object storage, where large blobs belong.
- **Persistent Entities** — content hashes, descriptive attributes, and references back to the payloads — in the SQL database, which indexes the blobs and makes them findable.
- **Transit messages** — the job descriptor and the worker's response — flowing through the message broker, never durably stored.

The first two groups are paired: every payload has exactly one metadata record that indexes it, and the metadata holds the reference that resolves to the payload in object storage. This realizes the two-backend split from the Conceptual Overview — SQL resolves a request to its artifacts, object storage delivers them — applied uniformly to all three artifact types.

| Entity | Store | What it holds |
|--------|-------|---------------|
| Source video | Object Storage (S3) | The raw uploaded video file, as submitted by the client. |
| Estimation result | Object Storage (S3) | The serialized 3D pose-estimation output produced by an inference worker. |
| Annotated video | Object Storage (S3) | The rendered video with pose overlays produced by a rendering worker. |
| Video metadata | SQL Database | Content hash, descriptive attributes (format, duration, resolution), and the reference to the source video object. |
| Estimation metadata | SQL Database | Parameter hash, lifecycle status, and the reference to the estimation result object. |
| Visualization metadata | SQL Database | Parameter hash, lifecycle status, and the reference to the annotated video object. |
| Job input | Message Broker | The task descriptor enqueued for a worker: job identity plus the references and parameters needed to run it — never the payload bytes themselves. |
| Job output | Result Backend | The worker's completion signal: outcome (success or failure) and references to the artifacts it wrote — read back to resolve the job's final state, not the artifact bytes themselves. |

## Persistent Entities

The three persistent entities form a linear chain of ownership: a `Video` is the root, an `Estimation` derives from one `Video` (`Estimation.video_id`), and a `Visualization` derives from one `Estimation` (`Visualization.estimation_id`). Beyond the fields they share — an `id`, a `storage_key` resolving to the payload in object storage, an optional `description`, and a UTC `created_at` — each entity records the parameters that produced its payload. Deletion cascades along the chain: removing a `Video` removes its derived `Estimation` and `Visualization` records, and releases the objects they index in object storage — so a derived artifact never outlives its source, and the system leaves behind neither orphaned rows nor dangling blobs.

**`Video` Entity**

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

**`Estimation` Entity**

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

**`Visualization` Entity**

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

## Binary Payloads

The three binary payloads live in object storage as a flat key->value mapping: the `storage_key` is the key, the artifact bytes are the value. Each key is a deterministic content hash — but what gets hashed differs by entity, and that difference is what makes deduplication work.

| Payload | Key is the hash of | Rationale |
|---------|--------------------|-----------|
| `Video` | the uploaded file's own bytes | The artifact already exists at upload time, so it is keyed on its own content — re-uploading the same video resolves to the same key. |
| `Estimation` | its source and preprocessing parameters: `video_id`, `target_width`, `target_height`, `target_fps`, `skip_start_seconds`, `duration_seconds` | The output does not exist yet at lookup time, so it is keyed on the parameters that *produce* it — identical parameters over the same video map to the same key. |
| `Visualization` | its source and rendering parameters: `estimation_id`, `show_bbox`, `show_bbox_confidence`, `show_keypoints`, `show_skeleton`, `crf`, `preset` | Same principle — keyed on the recipe that produces it, so identical rendering options over the same estimation map to the same key. |

Because the key is derived *before* the work runs, the existence check (**NFR‑10**) is a single lookup: if the key is already present, the stored artifact is returned and the expensive estimation or rendering is skipped entirely.

### Transit Messages

Unlike the persistent entities, the transit messages are never stored — they exist only in flight across a process boundary. There are two: a `JobInput` descriptor the service layer enqueues for a worker through the message broker, and a `JobOutput` the worker returns through the result backend on completion. Both carry only references and parameters, never payload bytes: the broker stays light, and the heavy artifacts move through object storage instead.

The service layer assembles each `JobInput` by combining the client's request with values it resolves from existing SQL records — so a descriptor is self-contained, and a worker needs no further database lookup to start. Because there are two worker types, there are two input shapes.

**`JobInput` — estimation task (Flow 2)**

| Field | Origin | Description |
|-------|--------|-------------|
| `video_id` | client request | The source `Video` to estimate over. |
| `source_storage_key` | resolved from `Video` | Object-storage key of the source video, so the worker can fetch it directly. |
| `target_width`, `target_height` | client request | Target frame dimensions applied during preprocessing. |
| `target_fps` | client request | Frame sampling rate before inference. |
| `skip_start_seconds`, `duration_seconds` | client request | Temporal window of the video to analyze. |
| `batch_size` | client request | Number of frames loaded and processed per batch (bounded streaming). |
| `description` | client request | Optional human-readable label, carried through to the record. |

**`JobInput` — visualization task (Flow 3)**

| Field | Origin | Description |
|-------|--------|-------------|
| `estimation_id` | client request | The source `Estimation` to render. |
| `source_video_key` | resolved from `Video` | Object-storage key of the original video to draw overlays onto. |
| `safetensors_key` | resolved from `Estimation` | Object-storage key of the serialized estimation result to read poses from. |
| `target_width`, `target_height`, `target_fps`, `skip_start_seconds`, `duration_seconds` | resolved from `Estimation` | The exact preprocessing parameters used when the estimation was produced. |
| `show_bbox`, `show_bbox_confidence`, `show_keypoints`, `show_skeleton` | client request | Which overlay layers to draw. |
| `crf`, `preset` | client request | x264 encoding quality and speed settings. |
| `batch_size` | client request | Frames processed per batch (bounded streaming). |
| `description` | client request | Optional human-readable label. |

The visualization descriptor carries a detail worth singling out: its preprocessing parameters (`target_width` through `duration_seconds`) are resolved **from the `Estimation` record, not taken from the client**. Rendering overlays requires decoding the source video into exactly the same frames the inference pass saw — same resolution, same sampling rate, same temporal window — or the 2D keypoints would land on misaligned frames. Pulling these values from the stored estimation guarantees the renderer reproduces the inference pass's frame stream rather than trusting the client to restate it consistently.

**`JobOutput` — both task types**

| Field | Description |
|-------|-------------|
| `resource_type` | A `TaskType` discriminator: whether the produced result is an `Estimation` or a `Visualization`. |
| `resource_id` | Primary key of the newly created metadata record, through which the client can later query the SQL database for the metadata or fetch the artifact itself. |

The output is deliberately minimal — a pointer, not a payload. The worker does the heavy lifting on its own side: it writes the artifact to object storage and its metadata row to SQL, then returns only *where the result lives* — its type and id. The service layer reads this off the result backend, updates the job's status in SQL accordingly, and the polling client resolves the result from that id. This keeps the result backend as light as the broker: it shuttles a locator, while object storage and SQL hold everything substantial.

## Next Steps

With the domain entities, their storage layout, and the messages that move between components all defined, the data the system operates on now has stable schemas. What remains is the request lifecycle of each endpoint: the ordered sequence of internal steps the server performs between accepting a request and answering it.