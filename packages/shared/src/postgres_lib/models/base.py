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

# packages/shared/src/postgres_lib/models/base.py
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    """
    Central registry for all ORM models in the application.

    Provides a unified schema foundation by inheriting a surrogate
    primary key, an immutable creation timestamp, a standardized
    object storage key column, and a human-readable description into
    every subclass. This ensures consistent metadata tracking and
    operational clarity across all artifact tables.

    Attributes
    ----------
    id : Mapped[int]
        Surrogate primary key for the record. Automatically assigned
        as a monotonically increasing integer upon insertion.
    created_at : Mapped[datetime]
        Timezone-aware timestamp indicating when the record was first
        inserted. Set automatically by the database using the current
        UTC time at insert time. Value remains immutable after creation.
    storage_key : Mapped[str]
        Object storage path or identifier for the associated file artifact.
        Uniqueness and indexing should be defined per-table in __table_args__.
        The column comment is automatically generated from the subclass name.
    description : Mapped[str or None]
        Human-readable label for quick identification in listing endpoints
        and operational dashboards. Nullable to allow optional annotation
        at creation time. Default is None.
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key identifier",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    description: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=None,
        comment="Human-readable label for operational identification",
    )

    @declared_attr
    def storage_key(cls) -> Mapped[str]:
        return mapped_column(
            String,
            nullable=False,
            comment=f"Object storage path for {cls.__name__} artifact",
        )