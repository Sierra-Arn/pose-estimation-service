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

# packages/shared/src/postgres_lib/models/video.py
from sqlalchemy import Float, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Video(Base):
    """
    Registry of uploaded video assets and their core metadata.
    Stores static properties required for downstream pipeline configuration
    and result alignment, such as resolution, frame rate, and storage location.

    Attributes
    ----------
    width : Mapped[int]
        Frame width in pixels.
    height : Mapped[int]
        Frame height in pixels.
    fps : Mapped[float]
        Nominal frame rate of the video source.
    duration_seconds : Mapped[float]
        Total playback duration in seconds.

    Notes
    -----
    The inherited storage_key column is uniquely indexed at the table level
    to enable O(log N) lookups by MinIO path and prevent duplicate metadata
    registration for the same object storage key.
    """

    __tablename__ = "videos"

    __table_args__ = (
        Index("ix_videos_storage_key", "storage_key", unique=True),
    )

    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Frame width in pixels",
    )

    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Frame height in pixels",
    )

    fps: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Nominal frame rate of the video source",
    )

    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Total playback duration in seconds",
    )