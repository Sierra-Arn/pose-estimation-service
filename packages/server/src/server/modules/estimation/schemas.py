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

# packages/server/src/server/modules/estimation/schemas.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class EstimationResponse(BaseModel):
    """
    Response body containing metadata for a completed pose estimation.
    Serves as the canonical read schema for all estimation retrieval endpoints.

    Attributes
    ----------
    id : int
        Primary key of the estimation record.
    video_id : int
        Foreign key referencing the source video.
    storage_key : str
        Object storage path to the serialized safetensors archive.
    requested_width : int
        Target frame width applied during preprocessing.
    requested_height : int
        Target frame height applied during preprocessing.
    requested_fps : float
        Frame sampling rate applied before inference.
    skip_start_seconds : float
        Temporal offset skipped from video start.
    duration_seconds : float
        Total analyzed segment duration.
    description : str or None
        Human-readable label provided at submission. None if unset.
    created_at : datetime
        Timezone-aware timestamp of record creation in UTC.
    """

    id: int = Field(
        ...,
        description="Primary key of the estimation record.",
    )
    video_id: int = Field(
        ...,
        description="Foreign key referencing the source video.",
    )
    storage_key: str = Field(
        ...,
        description="Object storage path to the safetensors archive.",
    )
    requested_width: int = Field(
        ...,
        description="Target frame width in pixels applied during preprocessing.",
    )
    requested_height: int = Field(
        ...,
        description="Target frame height in pixels applied during preprocessing.",
    )
    requested_fps: float = Field(
        ...,
        description="Frame sampling rate in fps applied before inference.",
    )
    skip_start_seconds: float = Field(
        ...,
        description="Temporal offset in seconds skipped from video start.",
    )
    duration_seconds: float = Field(
        ...,
        description="Total analyzed segment duration in seconds.",
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
                    "id": 42,
                    "video_id": 12,
                    "storage_key": "estimations/a1b2c3d4e5f6.safetensors",
                    "requested_width": 640,
                    "requested_height": 480,
                    "requested_fps": 15.0,
                    "skip_start_seconds": 0.0,
                    "duration_seconds": 30.0,
                    "description": "Sprint analysis day 3",
                    "created_at": "2024-05-20T14:30:00Z",
                }
            ]
        },
    )
