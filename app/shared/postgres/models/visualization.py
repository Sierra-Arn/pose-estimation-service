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

# app/shared/postgres/models/visualization.py
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Visualization(Base):
    """
    Storage record for a rendered pose visualization video.
    Links a completed 3D pose analysis result to its corresponding
    annotated video file in object storage and preserves the exact
    overlay configuration and encoding parameters used during rendering.

    Attributes
    ----------
    estimation_id : int
        Foreign key referencing the source pose analysis in the estimations table.
        Output resolution and frame rate are inherited from the parent record.
    show_bbox : bool
        Flag indicating whether bounding boxes were rendered in the output video.
        Default is False.
    show_keypoints : bool
        Flag indicating whether 2D keypoint markers were overlaid on the video.
        Default is False.
    show_skeleton : bool
        Flag indicating whether skeletal connections between keypoints were drawn.
        Default is False.
    show_bbox_confidence : bool
        Flag indicating whether detection confidence scores were rendered
        alongside bounding boxes. Default is False.
    crf : int
        Constant Rate Factor used for x264 encoding. Range 18-28; lower = higher quality.
        Default is 20.
    preset : str
        x264 encoding preset controlling speed vs compression trade-off.
        Default is "medium".

    Notes
    -----
    The inherited storage_key column is uniquely indexed to enable
    O(log N) lookups for cache validation and idempotent task submission.
    The estimation_id column is indexed to accelerate foreign key joins and
    cascade deletion operations.
    """

    __tablename__ = "visualizations"

    __table_args__ = (
        Index("ix_visualizations_estimation_id", "estimation_id"),
        Index("ix_visualizations_storage_key", "storage_key", unique=True),
    )

    estimation_id: Mapped[int] = mapped_column(
        ForeignKey("estimations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key referencing the source pose analysis record",
    )

    show_bbox: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Flag indicating whether bounding boxes were rendered",
    )

    show_keypoints: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Flag indicating whether 2D keypoint markers were overlaid",
    )

    show_skeleton: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Flag indicating whether skeletal connections were drawn",
    )

    show_bbox_confidence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Flag indicating whether confidence scores were rendered near bounding boxes",
    )

    crf: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
        comment="Constant Rate Factor for x264 encoding. Lower values increase quality and file size.",
    )

    preset: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="medium",
        comment="x264 speed vs compression preset. Affects encoding time and final file size.",
    )