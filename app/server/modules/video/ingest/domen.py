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

# app/server/modules/video/ingest/domen.py
import io
import hashlib
import av
from .types import VideoMetadata, VideoIngestionValidationResponse
from .....shared.postgres import VideoRepository, get_sync_db_session


def probe_video_metadata(video_bytes: bytes) -> VideoMetadata:
    """
    Extract video metadata directly from raw bytes using PyAV.

    Reads stream information from an in-memory bytes object without
    writing to disk or uploading to object storage. Intended for
    fast execution in a worker thread via asyncio.to_thread.

    Parameters
    ----------
    video_bytes : bytes
        Raw video file content to analyze.

    Returns
    -------
    VideoMetadata
        Structured container with parsed width, height, duration, and
        frame rate.

    Raises
    ------
    ValueError
        Raised when no video stream is found in the provided bytes.
    RuntimeError
        Raised when PyAV fails to open the container, decode headers,
        or extract stream metadata.
    """
    try:
        with av.open(io.BytesIO(video_bytes)) as container:
            streams = container.streams.video
            if not streams:
                raise ValueError("No video stream found in the provided bytes.")
            stream = streams[0]

            width = stream.width
            height = stream.height

            duration_seconds = None
            if stream.duration is not None and stream.time_base is not None:
                duration_seconds = max(0.0, float(stream.duration * stream.time_base))

            fps = None
            if stream.average_rate is not None:
                fps_val = float(stream.average_rate)
                fps = fps_val if fps_val > 0 else None

            return VideoMetadata(
                width=width,
                height=height,
                duration_seconds=duration_seconds,
                fps=fps,
            )
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract video metadata with PyAV: {e}") from e


def validate_upload_task(
    video_bytes: bytes,
) -> VideoIngestionValidationResponse:
    """
    Compute content hash, check for existing database records, and extract metadata.

    Performs all CPU-bound and synchronous I/O operations in a single thread.
    Manages its own synchronous database session internally to check for duplicates.
    If the video content hash matches an existing record, metadata extraction is skipped.
    Otherwise, the video bytes are analyzed for resolution, duration, and frame rate.

    Parameters
    ----------
    video_bytes : bytes
        Raw video file content to hash, check, and analyze.

    Returns
    -------
    UploadValidationResult
        Structured result containing a duplicate flag, the existing video primary
        key if found, the deterministic storage key, or fresh metadata if the
        content is new. Mutually exclusive fields are populated based on the
        deduplication outcome.

    Raises
    ------
    RuntimeError
        If database connectivity fails or metadata extraction encounters an error.
    """
    content_hash = hashlib.sha256(video_bytes).hexdigest()
    storage_key = f"videos/{content_hash}"

    with get_sync_db_session() as session:
        existing_video = VideoRepository.get_by_storage_key_sync(session, storage_key)
        if existing_video is not None:
            return VideoIngestionValidationResponse(
                is_duplicate=True,
                video=existing_video,
                storage_key=None,
                metadata=None,
            )

    metadata = probe_video_metadata(video_bytes)

    return VideoIngestionValidationResponse(
        is_duplicate=False,
        video=None,
        storage_key=storage_key,
        metadata=metadata,
    )