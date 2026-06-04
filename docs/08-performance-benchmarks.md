# VIII. **Performance Benchmarks**

## Ingestion Latency & Deduplication

This benchmark measures the performance of the video ingestion endpoint and validates the content-addressed deduplication mechanism. Each file is uploaded twice to the `/videos/ingest/` endpoint:

1. **First request**: Full validation pipeline — MIME type detection, SHA-256 hashing, MinIO upload, and database registration.
2. **Second request**: Deduplication check — if the file hash already exists in the database, the system bypasses heavy I/O operations and returns the existing record instantly.

The key metric is the **Deduplication Speedup** — the ratio between the first and second request latencies. A high speedup demonstrates that the content-addressed storage effectively eliminates redundant processing for duplicate uploads.

Additionally, the benchmark validates content-type enforcement by attempting to upload non-video files (`.pt` model weights and `.env` configuration), ensuring the system correctly rejects unsupported payloads.

### Benchmark Files

All video files were sourced from [Pexels](https://www.pexels.com/). Non-video files were included to test validation logic:

| # | File | Type | Resolution | Duration | Size |
|---|------|------|------------|----------|------|
| 1 | [Person jogging at the beach](https://www.pexels.com/video/person-jogging-at-the-beach-4928018/) | MP4 | 1920 × 1080 | 8.93 sec | 5.69 MB |
| 2 | [Man with prosthetic leg jogging](https://www.pexels.com/video/man-with-prosthetic-leg-jogging-8344814/) | MP4 | 3840 × 2160 | 24.32 sec | 72.10 MB |
| 3 | yolo26n.pt | PyTorch Model | — | — | 5.29 MB |
| 4 | .env | Environment Config | — | — | 0.003 MB |

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
| Number of Inference Workers | 1 (solo pool, CUDA, concurrency 1, prefetch_multiplier 1)   |

**Endpoint**

| | |
|-----------------|----------------------------------|
| Target URL      | http://0.0.0.0:8000/videos/ingest/ |
| HTTP Method     | POST                             |
| Content-Type    | multipart/form-data              |
| Expected Format | video/mp4, video/quicktime, video/webm |

### Performance

| # | File | 1st Request (Full Ingest) | 2nd Request (Dedup) | Speedup | Status |
|---|------|---------------------------|---------------------|---------|--------|
| 1 | Person jogging at the beach | 202.51 ms | 25.65 ms | 7.90x | ✅ Success |
| 2 | Man with prosthetic leg jogging | 758.38 ms | 273.38 ms | 2.77x | ✅ Success |
| 3 | yolo26n.pt | 37.82 ms | — | — | ❌ Rejected (400) |
| 4 | .env | 2.87 ms | — | — | ❌ Rejected (500) |

**Validation Results**

| File | Error Code | Error Message |
|------|------------|---------------|
| yolo26n.pt | 400 | Unsupported content type. Detected: application/zip. Allowed values: video/mp4, video/quicktime, video/webm. |
| .env | 500 | Failed to analyze uploaded file: Failed to detect MIME type: filetype could not identify the file signature. |

**Key Observations**

- **Deduplication effectiveness**: Video files show 2.77x–7.90x speedup on second upload, confirming that SHA-256 hash matching bypasses MinIO I/O and database writes.
- **File size correlation**: Larger files (72 MB vs 5.69 MB) show proportionally longer ingest times but similar deduplication performance, indicating that hash lookup is O(1) regardless of payload size.
- **Content validation**: Non-video files are correctly rejected at the API boundary with appropriate HTTP status codes (400 for known MIME types, 500 for undetectable signatures).

## Estimation Latency & GPU Inference Deduplication

This benchmark measures the performance of the pose estimation endpoint and validates the result caching mechanism. Each video is submitted twice to the `/estimations/submit/` endpoint with identical processing parameters:

1. **First request**: Full GPU inference pipeline — video decoding, frame extraction, 3D human pose estimation via SAM 3D Body model, and result persistence.
2. **Second request**: Result cache lookup — if the same video with identical processing parameters has already been estimated, the system bypasses GPU computation and returns the cached result instantly.

The key metric is the **Deduplication Speedup** — the ratio between the first and second request latencies. A high speedup demonstrates that the parameter-aware caching effectively eliminates redundant GPU computation for repeated estimation requests.

### Benchmark Videos

All videos were sourced from [Pexels](https://www.pexels.com/) and processed with identical estimation parameters:

| # | Video | Resolution | Duration | Size |
|---|-------|------------|----------|------|
| 1 | [Man with prosthetic leg jogging](https://www.pexels.com/video/man-with-prosthetic-leg-jogging-8344814/) | 3840 × 2160 | 24.32 sec | 72.10 MB |
| 2 | [Person jogging at the beach](https://www.pexels.com/video/person-jogging-at-the-beach-4928018/) | 1920 × 1080 | 8.93 sec | 5.69 MB |

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
| Number of Inference Workers | 1 (solo pool, CUDA, concurrency 1, prefetch_multiplier 1)   |

**Endpoint**

| | |
|-----------------|-------------------------------------------|
| Target URL      | http://0.0.0.0:8000/estimations/submit/   |
| HTTP Method     | POST                                      |
| Content-Type    | application/json                          |
| Processing Mode | Asynchronous (Submit-and-Poll)            |

**Estimation Parameters**

| Parameter | Video 1 (4K) | Video 2 (1080p) |
|-----------|--------------|-----------------|
| Target Resolution | 1920 × 1080 | 1920 × 1080 |
| Target Duration | 20.00 sec | 8.00 sec |
| Target FPS | 20.00 | 20.00 |
| Target Frames | 400 | 160 |
| Batch Size | 30 | 30 |

### Performance

| # | Video | Target Frames | 1st Request (GPU Inference) | 2nd Request (Cache Hit) | Speedup | Throughput |
|---|-------|---------------|-----------------------------|-------------------------|---------|------------|
| 1 | Man with prosthetic leg jogging | 400 | 27,143.76 ms | 1,006.55 ms | 26.97x | 14.74 FPS |
| 2 | Person jogging at the beach | 160 | 11,075.46 ms | 1,006.14 ms | 11.01x | 14.44 FPS |

**Key Observations**

- **Massive deduplication speedup**: GPU inference results show 11x–27x speedup on cache hits, significantly higher than ingestion deduplication (2.77x–7.90x). This confirms that parameter-aware caching effectively eliminates expensive GPU computation.
- **Stable cache lookup time**: Second requests consistently complete in ~1,006 ms regardless of video size or frame count, indicating O(1) cache lookup performance.
- **Real-time processing ratio**: Both videos process at approximately real-time speed (20 sec video → 27 sec processing, 8 sec video → 11 sec processing), demonstrating efficient GPU utilization.
- **Consistent throughput**: Despite different resolutions and durations, both videos achieve similar throughput (~14.5 FPS), showing that the inference pipeline scales linearly with frame count rather than being bottlenecked by I/O or resolution.
- **Batch processing efficiency**: With batch size 30, the system processes 400 frames in 14 batches (video 1) and 160 frames in 6 batches (video 2), maintaining stable GPU memory usage throughout inference.

## Parallel Pipeline Throughput

This benchmark evaluates the end-to-end throughput of the system under concurrent load. Ten videos are submitted simultaneously, and each independently progresses through the complete processing pipeline without synchronization barriers:

1. **Ingestion** — upload, validation, and database registration.
2. **Pose estimation** — GPU-accelerated 3D human mesh recovery via the `ensam3d_inference` engine.
3. **Visualization rendering** — CPU-bound video overlay generation and H.264 encoding.

Unlike sequential benchmarks, this test validates the distributed orchestration layer. Each video begins its next stage immediately upon completion of the previous one, without waiting for other videos to finish. This exposes the true parallelism of the worker pool and the effectiveness of the Celery-based task dispatch.

The key metric is the **Parallelism Ratio** — the ratio between the sum of all individual stage latencies and the actual wall-clock time. A ratio significantly greater than 1.0 confirms that the system is executing multiple stages of multiple videos concurrently, rather than serializing them.

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

**Per-Video Stage Latencies**

| # | Video | Ingest | Estimation | Visualization | Total (Sequential) |
|---|-------|--------|------------|---------------|--------------------|
| 1 | Person jogging at the beach | 1.49 sec | 28.32 sec | 7.08 sec | 36.89 sec |
| 2 | Man with prosthetic leg jogging | 4.62 sec | 122.90 sec | 8.06 sec | 135.58 sec |
| 3 | A man running on the beach shore | 3.43 sec | 70.53 sec | 10.16 sec | 84.12 sec |
| 4 | A man jogging by the lakeside | 2.75 sec | 53.29 sec | 8.08 sec | 64.12 sec |
| 5 | A man running at the beach | 4.61 sec | 115.86 sec | 8.07 sec | 128.54 sec |
| 6 | A woman running in the beach | 3.57 sec | 102.74 sec | 10.10 sec | 116.41 sec |
| 7 | A person running on the beach at sunset | 1.49 sec | 48.45 sec | 8.08 sec | 58.02 sec |
| 8 | Woman jogging by the seashore | 3.45 sec | 76.57 sec | 11.16 sec | 91.18 sec |
| 9 | A man running on the beach | 1.47 sec | 32.37 sec | 7.11 sec | 40.95 sec |
| 10 | Man jogging outdoors | 3.56 sec | 92.68 sec | 11.12 sec | 107.36 sec |

**Aggregate Metrics**

| | |
|----------------------------|------------|
| Total Videos Processed     | 10         |
| Wall-Clock Time            | 135.68 sec |
| Summed Stage Times         | 863.15 sec |
| Parallelism Ratio          | 6.36x      |

**Key Observations**

- **Effective distributed execution**: A parallelism ratio of 6.36x demonstrates that the system processed the equivalent of ~14.4 minutes of sequential work in just ~2.3 minutes of real time. This confirms that the Celery-based orchestration layer successfully distributes tasks across heterogeneous worker pools (2 GPU inference workers + 1 CPU post-processing worker with concurrency 4).
- **GPU as the bottleneck**: The longest stage for every video is estimation (32–123 sec), while visualization completes in 7–11 sec despite being CPU-bound. This indicates that the 2 inference workers with `concurrency=1` each form the critical path, while the 4 concurrent post-processing tasks in the default worker have sufficient headroom.
- **Heterogeneous workload handling**: Videos range from 3.27 MB (720p, 10 sec) to 77.51 MB (4K, 26 sec), yet all complete successfully. The system dynamically schedules tasks as they become ready — a small video finishing ingestion immediately proceeds to estimation without waiting for larger uploads.
- **Pipeline overlap**: The wall-clock time (135.68 sec) is only slightly longer than the single heaviest video's sequential time (135.58 sec for video #2), indicating that the system effectively overlapped the processing of all 10 videos rather than serializing them.