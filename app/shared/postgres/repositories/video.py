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

# app/shared/postgres/repositories/video.py
from typing import ClassVar
from sqlalchemy import select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..models import Video, Estimation, Visualization


class VideoRepository(BaseRepository):
    """
    Stateless data access implementation for the Video ORM model.
    
    Provides asynchronous and synchronous query operations for video
    metadata, storage key validation, pagination, and dependency
    resolution for cascade cleanup.

    Attributes
    ----------
    model_class : ClassVar[type[Video]]
        SQLAlchemy ORM model class bound to the videos table.
        Used for static type checking of all inherited methods.
    """

    model_class: ClassVar[type[Video]] = Video

    @classmethod
    async def collect_dependent_storage_keys(
        cls,
        session: AsyncSession,
        video_id: int,
    ) -> list[str]:
        """
        Collect all storage keys for a video and its dependent artifacts.
        Executes a single SQL query using UNION ALL to retrieve storage
        keys from the videos, estimations, and visualizations tables
        based on foreign key relationships. Eliminates N+1 query patterns
        during cascade cleanup operations.

        Parameters
        ----------
        session : AsyncSession
            Active async database session bound to the transaction.
        video_id : int
            Primary key of the source video record.

        Returns
        -------
        list of str
            Flat list of storage keys associated with the video and all
            downstream estimation and visualization records. Returns an
            empty list if the video ID does not exist or has no dependents.
        """
        video_q = select(cls.model_class.storage_key).where(
            cls.model_class.id == video_id
        )
        est_q = select(Estimation.storage_key).where(
            Estimation.video_id == video_id
        )
        vis_q = (
            select(Visualization.storage_key)
            .join(Estimation, Visualization.estimation_id == Estimation.id)
            .where(Estimation.video_id == video_id)
        )

        stmt = union_all(video_q, est_q, vis_q)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]