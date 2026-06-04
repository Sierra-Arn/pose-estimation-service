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

# packages/shared/src/postgres_lib/models/estimation.py
from sqlalchemy import Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Estimation(Base):
    """
    Storage record for a single 3D pose estimation result.
    Links a processed video to its serialized safetensors archive in object storage
    and preserves the exact pipeline configuration used for the estimation.

    Attributes
    ----------
    video_id : int
        Foreign key referencing the source video in the videos table.
    requested_width : int
        Target frame width in pixels applied during preprocessing.
    requested_height : int
        Target frame height in pixels applied during preprocessing.
    requested_fps : float
        Frame sampling rate applied before inference in fps.
    skip_start_seconds : float
        Temporal offset in seconds to skip from video start. Default is 0.0.
    duration_seconds : float
        Total analyzed segment duration in seconds.

    Notes
    -----
    The inherited storage_key column is uniquely indexed to enable
    O(log N) lookups for cache validation and idempotent task submission.
    The video_id column is indexed to accelerate foreign key joins and
    cascade deletion operations.
    """

    __tablename__ = "estimations"

    __table_args__ = (
        Index("ix_estimations_video_id", "video_id"),
        Index("ix_estimations_storage_key", "storage_key", unique=True),
    )

    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key referencing the source video record",
    )

    requested_width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Target frame width in pixels applied during preprocessing",
    )

    requested_height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Target frame height in pixels applied during preprocessing",
    )

    requested_fps: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Frame sampling rate applied before inference in fps",
    )

    skip_start_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Temporal offset in seconds to skip from video start before processing",
    )

    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Total analyzed segment duration in seconds",
    )