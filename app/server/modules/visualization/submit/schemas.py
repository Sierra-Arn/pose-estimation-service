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

# app/server/modules/visualization/submit/schemas.py
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class VisualizationSubmitRequest(BaseModel):
    """
    Request body for submitting a new pose visualization rendering task.
    Contains overlay configuration, encoding parameters, and optional
    metadata for the asynchronous visualization pipeline execution.

    Attributes
    ----------
    estimation_id : int
        Primary key of the completed estimation record to visualize.
    show_bbox : bool, optional
        Toggle bounding box rendering in the output video.
        Default is False.
    show_bbox_confidence : bool, optional
        Toggle detection confidence score rendering.
        Default is False.
    show_keypoints : bool, optional
        Toggle 2D keypoint marker rendering.
        Default is True.
    show_skeleton : bool, optional
        Toggle skeletal connection rendering.
        Default is True.
    crf : int, optional
        Constant Rate Factor for x264 encoding. Lower values yield
        higher quality and larger files. Range is 0 to 51.
        Default is 20.
    preset : Literal["ultrafast", "superfast", "veryfast", "faster", "fast",
        "medium", "slow", "slower", "veryslow"], optional
        x264 encoding speed versus compression trade-off preset.
        ultrafast provides the fastest encoding but largest file size,
        while veryslow produces the smallest file with slowest encoding.
        Default is "slower".
    description : str or None, optional
        Human-readable label for operational identification.
        Default is None.
    batch_size : int, optional
        Number of frames processed per encoding batch. Does not affect
        final quality or visual output, only processing speed via batch count.
        Default is 30.
    """

    estimation_id: int = Field(
        ...,
        gt=0,
        description="Primary key of the source estimation record.",
    )
    show_bbox: bool = Field(
        default=False,
        description="Toggle bounding box rendering.",
    )
    show_bbox_confidence: bool = Field(
        default=False,
        description="Toggle detection confidence score rendering.",
    )
    show_keypoints: bool = Field(
        default=True,
        description="Toggle 2D keypoint marker rendering.",
    )
    show_skeleton: bool = Field(
        default=True,
        description="Toggle skeletal connection rendering.",
    )
    crf: int = Field(
        default=20,
        ge=0,
        le=51,
        description="x264 Constant Rate Factor for quality control.",
    )
    preset: Literal[
        "ultrafast",
        "superfast",
        "veryfast",
        "faster",
        "fast",
        "medium",
        "slow",
        "slower",
        "veryslow"
    ] = Field(
        default="slower",
        description="x264 encoding speed versus compression preset.",
    )
    description: str | None = Field(
        default=None,
        max_length=512,
        description="Human-readable label for operational identification.",
    )
    batch_size: int = Field(
        default=30,
        gt=0,
        description="Frames per decoding and encoding batch.",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "estimation_id": 1,
                    "show_bbox": False,
                    "show_bbox_confidence": False,
                    "show_keypoints": True,
                    "show_skeleton": True,
                    "crf": 20,
                    "preset": "slower",
                    "description": "Sprint analysis visualization",
                    "batch_size": 30,
                }
            ]
        },
    )