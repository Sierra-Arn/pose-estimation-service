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

# packages/worker-default/src/worker_default/tasks/visualize/__init__.py
import shutil
import tempfile
from pathlib import Path
from typing import Iterator
import numpy as np
from ensam3d_inference.preprocessor.detector.types import RGBFrame
from postgres_lib import get_sync_db_session, Visualization
from minio_lib import StorageOperations
from task_queue.infrastructure.types import TaskType, TaskResultPayload
from task_queue.infrastructure.validator import validate_task_request
from task_queue.infrastructure.tensors_io import load_pipeline_output
from task_queue.infrastructure.frame_extractor import decode_video_stream_batches
from task_queue import celery_app, celery_config
from .viz_uploader import encode_to_minio
from .render import render_frame


@celery_app.task(
    name=celery_config._task_name_visualize,
    queue=celery_config.queue_name_default,
)
def visualize_task(
    estimation_id: int,
    source_video_key: str,
    safetensors_key: str,
    target_width: int,
    target_height: int,
    target_fps: float,
    skip_start_seconds: float,
    duration_seconds: float,
    show_bbox: bool,
    show_bbox_confidence: bool,
    show_keypoints: bool,
    show_skeleton: bool,
    crf: int,
    preset: str,
    batch_size: int,
    description: str | None = None,
    expires: int = 3600,
) -> TaskResultPayload:
    """
    Render annotated pose estimation video and upload to object storage.

    Validates idempotency, loads inference artifacts, decodes source frames,
    applies visual overlays via OpenCV, encodes output with FFmpeg through
    a helper function, and registers the result in the database.

    Parameters
    ----------
    estimation_id : int
        Primary key of the completed Estimation record.
    source_video_key : str
        Object storage key of the original video file.
    safetensors_key : str
        Object storage key of the serialized inference results.
    target_width : int
        Output frame width in pixels applied during decoding.
    target_height : int
        Output frame height in pixels applied during decoding.
    target_fps : float
        Target frame rate for output frames.
    skip_start_seconds : float
        Temporal offset in seconds to skip from video start.
    duration_seconds : float
        Total duration of frames to process in seconds.
    show_bbox : bool, optional
        Toggle bounding box rendering. Default is False.
    show_bbox_confidence : bool, optional
        Toggle confidence score rendering. Default is False.
    show_keypoints : bool, optional
        Toggle keypoint marker rendering. Default is False.
    show_skeleton : bool, optional
        Toggle skeleton line rendering. Default is False.
    crf : int, optional
        FFmpeg x264 constant rate factor for quality control. Default is 20.
    preset : str, optional
        FFmpeg x264 encoding speed or size preset. Default is medium.
    batch_size : int, optional
        Number of frames per decoding batch. Default is 30.
    expires : int, optional
        Presigned URL lifetime in seconds. Default is 3600.
    description : str or None, optional
        Human-readable label for the visualization record. Default is None.

    Returns
    -------
    TaskResultPayload
        Dictionary containing resource_type visualization and resource_id
        of the newly created or matched Visualization record.

    Raises
    ------
    RuntimeError
        If artifacts fail to load, FFmpeg encoding errors, or database or
        storage operations fail.

    Notes
    -----
    Idempotency is enforced via the unified validate_task_request function.
    All visualization parameters that affect the output artifact are included
    in the canonical JSON hash. The batch_size parameter is intentionally
    excluded from the hash as it does not affect the final result, only
    the internal processing chunking.
    """

    params = {
        "estimation_id": estimation_id,
        "show_bbox": show_bbox,
        "show_bbox_confidence": show_bbox_confidence,
        "show_keypoints": show_keypoints,
        "show_skeleton": show_skeleton,
        "crf": crf,
        "preset": preset,
    }

    validation = validate_task_request(params, TaskType.VISUALIZATION)

    if validation.is_duplicate:
        return TaskResultPayload(
            resource_type=TaskType.VISUALIZATION,
            resource_id=validation.id,
        )

    tmp_dir = Path(tempfile.mkdtemp())
    safetensors_path = tmp_dir / "results.safetensors"

    try:

        bytes_data = StorageOperations.download_bytes_sync(safetensors_key)
        safetensors_path.write_bytes(bytes_data)

        pipeline_outputs = load_pipeline_output(safetensors_path)
        safetensors_path.unlink(missing_ok=True)

        total_frames = len(pipeline_outputs)

        output = np.zeros((target_height, target_width, 3), dtype=np.uint8)

        def _frame_generator() -> Iterator[RGBFrame]:
            frame_idx = 0

            for batch_frames in decode_video_stream_batches(
                storage_key=source_video_key,
                target_width=target_width,
                target_height=target_height,
                target_fps=target_fps,
                batch_size=batch_size,
                skip_start_seconds=skip_start_seconds,
                duration_seconds=duration_seconds,
                expires=expires,
            ):
                for frame in batch_frames:
                    if frame_idx >= total_frames:
                        return

                    result = pipeline_outputs[frame_idx]
                    rendered = render_frame(
                        frame=frame,
                        result=result,
                        output=output,
                        show_bbox=show_bbox,
                        show_bbox_confidence=show_bbox_confidence,
                        show_keypoints=show_keypoints,
                        show_skeleton=show_skeleton,
                    )
                    yield rendered
                    frame_idx += 1

        encode_to_minio(
            frame_generator=_frame_generator(),
            storage_key=validation.storage_key,
            width=target_width,
            height=target_height,
            fps_target=target_fps,
            crf=crf,
            preset=preset,
        )

        with get_sync_db_session() as session:
            vis_record = Visualization(
                estimation_id=estimation_id,
                storage_key=validation.storage_key,
                show_bbox=show_bbox,
                show_bbox_confidence=show_bbox_confidence,
                show_keypoints=show_keypoints,
                show_skeleton=show_skeleton,
                crf=crf,
                preset=preset,
                description=description,
            )
            session.add(vis_record)
            session.commit()
            session.refresh(vis_record)

        return TaskResultPayload(
            resource_type=TaskType.VISUALIZATION,
            resource_id=vis_record.id,
        )

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True) 