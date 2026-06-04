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

# packages/server/src/server/modules/estimation/submit/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class EstimationSubmitRequest(BaseModel):
    """
    Request body for submitting a new 3D pose estimation task.

    Contains preprocessing parameters and optional metadata for the
    distributed pipeline execution.

    Attributes
    ----------
    video_id : int
        Primary key of the source video record to analyze.
    target_width : int
        Frame width in pixels after preprocessing. Must be positive.
    target_height : int
        Frame height in pixels after preprocessing. Must be positive.
    target_fps : float
        Frame sampling rate in frames per second applied before inference.
    skip_start_seconds : float
        Temporal offset in seconds to skip from video start. Default is 0.0.
    duration_seconds : float
        Total segment duration to analyze in seconds. Must be positive.
    batch_size : int
        Number of frames processed per inference step. Default is 30.
    description : str or None
        Human-readable label for operational identification. Default is None.
    """

    video_id: int = Field(
        ...,
        gt=0,
        description="Primary key of the source video record.",
    )
    target_width: int = Field(
        ...,
        gt=0,
        description="Output frame width in pixels.",
    )
    target_height: int = Field(
        ...,
        gt=0,
        description="Output frame height in pixels.",
    )
    target_fps: float = Field(
        ...,
        gt=0.0,
        description="Target frame rate for decoding.",
    )
    skip_start_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Temporal offset to skip from video start.",
    )
    duration_seconds: float = Field(
        ...,
        gt=0.0,
        description="Total analyzed segment duration in seconds.",
    )
    batch_size: int = Field(
        default=30,
        gt=0,
        description="Frames per inference batch.",
    )
    description: str | None = Field(
        default=None,
        max_length=512,
        description="Human-readable label for operational identification.",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "video_id": 1,
                    "target_width": 1920,
                    "target_height": 1080,
                    "target_fps": 5.0,
                    "skip_start_seconds": 5.0,
                    "duration_seconds": 30.0,
                    "batch_size": 30,
                    "description": "Sprint analysis day 3"
                }
            ]
        },
    )