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

# packages/server/src/server/modules/video/ingest/domen.py
import io
import hashlib
import av
import filetype
from postgres_lib import VideoRepository, get_sync_db_session
from .types import (
    VideoMetadata, 
    VideoIngestionValidationResponse, 
    ALLOWED_INGESTION_CONTENT_TYPES_STR, 
    SUPPORTED_INGESTION_CONTENT_TYPES
)


def probe_type(file_bytes: bytes) -> tuple[str, str]:
    """
    Determine and validate the MIME type and file extension from raw bytes using filetype.

    Analyzes the binary signature (magic bytes) at the beginning of the file to identify
    its true content type and associated extension, independent of file name or
    client-declared Content-Type headers. Relies on the pure-Python filetype library
    for accurate detection across common media formats without any system-level
    dependencies. The detected MIME type is validated against
    SUPPORTED_INGESTION_CONTENT_TYPES to ensure only accepted video formats
    are processed downstream.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content to analyze. Only the first several kilobytes are typically
        required for accurate detection, making this function efficient even for
        large files.

    Returns
    -------
    tuple[str, str]
        A two-element tuple of (mime_type, extension) where mime_type is the detected
        MIME type string guaranteed to be present in SUPPORTED_INGESTION_CONTENT_TYPES
        (for example, video/mp4 or video/quicktime), and extension is the corresponding
        file extension without a leading dot (for example, mp4 or mov).

    Raises
    ------
    ValueError
        Raised when the detected MIME type is not present in the
        SUPPORTED_INGESTION_CONTENT_TYPES allowlist. The error message includes
        the detected type and the complete list of allowed values to assist
        client debugging.
    RuntimeError
        Raised when filetype fails to match any known file signature against
        the provided bytes, typically due to corruption, insufficient data,
        or an unsupported format.
    """
    kind = filetype.guess(file_bytes)

    if kind is None:
        raise RuntimeError(
            "Failed to detect MIME type: filetype could not identify the file signature."
        )

    detected_type = kind.mime
    detected_extension = kind.extension

    if detected_type not in SUPPORTED_INGESTION_CONTENT_TYPES:
        raise ValueError(
            f"Unsupported content type. Detected: {detected_type}. "
            f"Allowed values: {ALLOWED_INGESTION_CONTENT_TYPES_STR}."
        )

    return detected_type, detected_extension


def probe_video_metadata(video_bytes: bytes) -> VideoMetadata:
    """
    Extract video metadata directly from raw bytes using PyAV.

    Reads stream information from an in-memory bytes object without
    writing to disk or uploading to object storage. Validates that all
    required metadata fields (duration and frame rate) are present and
    non-zero. Intended for fast execution in a worker thread via
    asyncio.to_thread.

    Parameters
    ----------
    video_bytes : bytes
        Raw video file content to analyze.

    Returns
    -------
    VideoMetadata
        Structured container with parsed width, height, duration, and
        frame rate. All fields are guaranteed to be non-None for valid
        video files.

    Raises
    ------
    ValueError
        Raised when no video stream is found in the provided bytes,
        or when duration or frame rate cannot be determined from the
        stream metadata.
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

            if duration_seconds is None:
                raise ValueError(
                    "Could not determine video duration from stream metadata."
                )
            
            if fps is None:
                raise ValueError(
                    "Could not determine video frame rate from stream metadata."
                )

            return VideoMetadata(
                width=width,
                height=height,
                duration_seconds=duration_seconds,
                fps=fps,
            )
        
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to extract video metadata with PyAV: {e}") from e


def validate_video_upload(
    video_bytes: bytes,
) -> VideoIngestionValidationResponse:
    """
    Detect MIME type, compute content hash, check for duplicates, and extract metadata.

    Performs all CPU-bound and synchronous I/O operations in a single thread.
    Manages its own synchronous database session internally to check for duplicates.
    MIME detection runs first as a fast-fail gate before any expensive processing.
    If the video content hash matches an existing record, metadata extraction is skipped.
    Otherwise, the video bytes are analyzed for resolution, duration, and frame rate.

    Parameters
    ----------
    video_bytes : bytes
        Raw video file content to validate, hash, and analyze.

    Returns
    -------
    VideoIngestionValidationResponse
        Structured result containing a duplicate flag, the existing video primary
        key if found, the deterministic storage key, the detected MIME content
        type, or fresh metadata if the content is new. Mutually exclusive fields
        are populated based on the deduplication outcome.

    Raises
    ------
    ValueError
        If the detected MIME type is not in SUPPORTED_INGESTION_CONTENT_TYPES,
        no video stream is found during PyAV analysis, or required metadata
        fields such as duration or frame rate cannot be determined.
    RuntimeError
        If libmagic fails to analyze the bytes, PyAV fails to open the
        container and decode headers, or database connectivity fails
        during the deduplication lookup.
    """
    content_type, extension = probe_type(video_bytes)
    content_hash = hashlib.sha256(video_bytes).hexdigest()
    storage_key = f"videos/{content_hash}.{extension}"

    with get_sync_db_session() as session:
        existing_video = VideoRepository.get_by_storage_key_sync(session, storage_key)
        if existing_video is not None:
            return VideoIngestionValidationResponse(
                is_duplicate=True,
                video=existing_video,
                storage_key=None,
                content_type=None,
                metadata=None,
            )

    metadata = probe_video_metadata(video_bytes)

    return VideoIngestionValidationResponse(
        is_duplicate=False,
        video=None,
        storage_key=storage_key,
        content_type=content_type,
        metadata=metadata,
    )