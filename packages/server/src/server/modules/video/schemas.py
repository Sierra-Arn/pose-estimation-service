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

# packages/server/src/server/modules/video/schemas.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class VideoResponse(BaseModel):
    """
    Response body containing metadata for a registered video asset.
    Serves as the canonical read schema for all video retrieval endpoints.

    Attributes
    ----------
    id : int
        Primary key of the video record.
    storage_key : str
        Object storage path or identifier for the original video file.
    width : int
        Frame width in pixels.
    height : int
        Frame height in pixels.
    fps : float
        Nominal frame rate of the video source.
    duration_seconds : float
        Total playback duration in seconds.
    description : str or None
        Human-readable label for operational identification. None if unset.
    created_at : datetime
        Timezone-aware timestamp of record creation in UTC.
    """

    id: int = Field(
        ...,
        description="Primary key of the video record.",
    )
    storage_key: str = Field(
        ...,
        description="Object storage path or identifier for the original video file.",
    )
    width: int = Field(
        ...,
        description="Frame width in pixels.",
    )
    height: int = Field(
        ...,
        description="Frame height in pixels.",
    )
    fps: float = Field(
        ...,
        description="Nominal frame rate of the video source.",
    )
    duration_seconds: float = Field(
        ...,
        description="Total playback duration in seconds.",
    )
    description: str | None = Field(
        default=None,
        max_length=512,
        description="Human-readable label for operational identification.",
    )
    created_at: datetime = Field(
        ...,
        description="Timezone-aware timestamp of record creation in UTC.",
    )

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "storage_key": "videos/a1b2c3d4e5.mp4",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30.0,
                    "duration_seconds": 125.4,
                    "description": "Sprint analysis day 3",
                    "created_at": "2024-05-20T14:30:00Z",
                }
            ]
        },
    )