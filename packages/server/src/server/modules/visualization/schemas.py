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

# packages/server/src/server/modules/visualization/schemas.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class VisualizationResponse(BaseModel):
    """
    Response body containing metadata for a completed pose visualization.
    Serves as the canonical read schema for all visualization retrieval endpoints.

    Attributes
    ----------
    id : int
        Primary key of the visualization record.
    estimation_id : int
        Foreign key referencing the source estimation record.
    storage_key : str
        Object storage path to the rendered MP4 video file.
    show_bbox : bool
        Flag indicating whether bounding boxes were rendered in the output video.
    show_bbox_confidence : bool
        Flag indicating whether detection confidence scores were rendered.
    show_keypoints : bool
        Flag indicating whether 2D keypoint markers were overlaid.
    show_skeleton : bool
        Flag indicating whether skeletal connections between keypoints were drawn.
    crf : int
        Constant Rate Factor used for x264 encoding. Range 0 to 51.
    preset : str
        x264 encoding preset controlling speed versus compression trade-off.
    description : str or None
        Human-readable label for operational identification. None if unset.
    created_at : datetime
        Timezone-aware timestamp of record creation in UTC.
    """

    id: int = Field(
        ...,
        description="Primary key of the visualization record.",
    )
    estimation_id: int = Field(
        ...,
        description="Foreign key referencing the source estimation record.",
    )
    storage_key: str = Field(
        ...,
        description="Object storage path to the rendered MP4 video file.",
    )
    show_bbox: bool = Field(
        ...,
        description="Flag indicating whether bounding boxes were rendered.",
    )
    show_bbox_confidence: bool = Field(
        ...,
        description="Flag indicating whether detection confidence scores were rendered.",
    )
    show_keypoints: bool = Field(
        ...,
        description="Flag indicating whether 2D keypoint markers were overlaid.",
    )
    show_skeleton: bool = Field(
        ...,
        description="Flag indicating whether skeletal connections were drawn.",
    )
    crf: int = Field(
        ...,
        description="Constant Rate Factor used for x264 encoding. Range 0 to 51.",
    )
    preset: str = Field(
        ...,
        description="x264 encoding preset controlling speed versus compression trade-off.",
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
                    "estimation_id": 7,
                    "storage_key": "visualizations/a1b2c3d4e5f6.mp4",
                    "show_bbox": False,
                    "show_bbox_confidence": False,
                    "show_keypoints": True,
                    "show_skeleton": True,
                    "crf": 20,
                    "preset": "slower",
                    "description": "Sprint analysis day 3",
                    "created_at": "2024-05-20T14:30:00Z",
                }
            ]
        },
    )