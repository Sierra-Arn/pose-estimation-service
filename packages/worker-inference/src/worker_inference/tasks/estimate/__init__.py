# Copyright (c) 2026 Ilya Snegov (aka Sierra Arn)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# packages/worker-inference/src/worker_inference/tasks/estimate/__init__.py
from typing import Any
from ensam3d_inference import PreprocessorInput, PipelineOutput
from task_queue.infrastructure.types import TaskType, TaskResultPayload
from task_queue.infrastructure.validator import validate_task_request
from task_queue.infrastructure.frame_extractor import decode_video_stream_batches
from task_queue import celery_config, celery_app
from .output_uploader import upload_pipeline_output_to_minio
from .metadata_persistor import create_estimation_record


@celery_app.task(
    name=celery_config._task_name_estimate,
    queue=celery_config.queue_name_inference,
)
def estimate_task(
    source_storage_key: str,
    video_id: int,
    target_width: int,
    target_height: int,
    target_fps: float,
    skip_start_seconds: float,
    duration_seconds: float,
    batch_size: int,
    expires: int = 3600,
    description: str | None = None,
) -> TaskResultPayload:
    """
    Execute full 3D human pose estimation pipeline on a prevalidated source video.

    Validates request idempotency via the unified task validator, decodes frames
    in batches, runs GPU inference, accumulates results, serializes to safetensors,
    uploads to object storage, and persists metadata to the relational database.
    Returns a structured payload for downstream API consumption.

    Parameters
    ----------
    source_storage_key : str
        Object storage key of the validated source video file.
    video_id : int
        Foreign key referencing the source video record for metadata persistence.
    target_width : int
        Frame width applied during preprocessing.
    target_height : int
        Frame height applied during preprocessing.
    target_fps : float
        Frame sampling rate applied before inference.
    skip_start_seconds : float
        Temporal offset to skip from video start.
    duration_seconds : float
        Total analyzed segment duration.
    batch_size : int
        Number of frames per inference batch.
    expires : int, optional
        Lifetime of the presigned URL in seconds. Default is 3600.
    description : str or None, optional
        Human-readable label for operational identification. Default is None.

    Returns
    -------
    TaskResultPayload
        Structured dictionary containing:
        resource_type : str
            Always "estimation".
        resource_id : int
            Primary key of the created or matched estimation record.

    Raises
    ------
    RuntimeError
        If video decoding, inference, serialization, upload, or database
        persistence fails at any stage.

    Notes
    -----
    Idempotency is enforced via the unified validate_task_request function.
    All preprocessing parameters that affect the output artifact are included
    in the canonical JSON hash. The batch_size parameter is intentionally
    excluded from the hash as it does not affect the final result, only
    the internal processing chunking.

    All batch results are accumulated in full_results before serialization.
    This is required because the safetensors format does not support
    incremental or streaming writes: the complete tensor dictionary must
    be known upfront before the archive can be written. Memory consumption
    therefore grows linearly with video duration and scales with the number
    of detected humans per frame.
    """

    params: dict[str, Any] = {
        "video_id": video_id,
        "target_width": target_width,
        "target_height": target_height,
        "target_fps": target_fps,
        "skip_start_seconds": skip_start_seconds,
        "duration_seconds": duration_seconds,
    }

    validation = validate_task_request(params, TaskType.ESTIMATION)

    if validation.is_duplicate:
        duplicate_payload: TaskResultPayload = {
            "resource_type": TaskType.ESTIMATION,
            "resource_id": validation.id,
        }
        return duplicate_payload

    from ...main import get_pipeline
    pipeline = get_pipeline()

    full_results: PipelineOutput = []

    for batch_frames in decode_video_stream_batches(
        storage_key=source_storage_key,
        target_width=target_width,
        target_height=target_height,
        target_fps=target_fps,
        batch_size=batch_size,
        skip_start_seconds=skip_start_seconds,
        duration_seconds=duration_seconds,
        expires=expires,
    ):
        batch_results = pipeline(PreprocessorInput(imgs=batch_frames))
        full_results.extend(batch_results)

    if not full_results:
        raise RuntimeError(
            "Inference pipeline returned empty results. "
            "Video may be unreadable or contain no humans."
        )

    upload_pipeline_output_to_minio(
        pipeline_output=full_results,
        storage_key=validation.storage_key,
    )

    new_result_id = create_estimation_record(
        video_id=video_id,
        storage_key=validation.storage_key,
        requested_width=target_width,
        requested_height=target_height,
        requested_fps=target_fps,
        skip_start_seconds=skip_start_seconds,
        duration_seconds=duration_seconds,
        description=description,
    )

    success_payload: TaskResultPayload = {
        "resource_type": TaskType.ESTIMATION,
        "resource_id": new_result_id,
    }
    return success_payload