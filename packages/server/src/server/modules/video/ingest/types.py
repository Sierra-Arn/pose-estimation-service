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

# packages/server/src/server/modules/video/ingest/types.py
from typing import NamedTuple
from postgres_lib import Video


class VideoMetadata(NamedTuple):
    """
    Container for extracted video stream metadata.

    Attributes
    ----------
    width : int
        Original frame width in pixels.
    height : int
        Original frame height in pixels.
    duration_seconds : float
        Total video duration in seconds.
    fps : float
        Average frame rate.
    """

    width: int
    height: int
    duration_seconds: float
    fps: float


class VideoIngestionValidationResponse(NamedTuple):
    """
    Result container for the synchronous video ingestion validation task.
    Mutually exclusive fields: exactly one outcome path is populated.

    Attributes
    ----------
    is_duplicate : bool
        True if an identical file already exists in the database.
    video : Video or None
        Fully loaded ORM instance of the existing record if duplicate.
        None otherwise.
    storage_key : str or None
        Deterministic object storage key derived from SHA-256 hash if unique.
        None otherwise.
    content_type : str or None
        MIME type detected via libmagic if unique. None otherwise.
    metadata : VideoMetadata or None
        Extracted technical metadata if unique. None otherwise.
    """

    is_duplicate: bool
    video: Video | None
    storage_key: str | None
    content_type: str | None
    metadata: VideoMetadata | None


SUPPORTED_INGESTION_CONTENT_TYPES = frozenset({
    "video/mp4",
    "video/quicktime",
    "video/webm",
})
"""
Immutable allowlist of MIME types accepted for video ingestion.

Defines the strict set of content types validated during request
ingestion. The frozenset data type ensures thread safety, prevents
accidental modification, and provides O(1) lookup performance
during routing validation.
"""


ALLOWED_INGESTION_CONTENT_TYPES_STR = ", ".join(sorted(SUPPORTED_INGESTION_CONTENT_TYPES))
"""
Pre-computed string representation of allowed MIME types.
Used in HTTP error responses to inform the client about
supported video formats without runtime formatting overhead.
"""