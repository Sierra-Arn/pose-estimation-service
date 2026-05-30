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

# app/shared/postgres/repositories/estimation.py
from typing import ClassVar
from sqlalchemy import select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..models import Estimation, Visualization


class EstimationRepository(BaseRepository):
    """
    Stateless data access implementation for the Estimation ORM model.
    
    Provides type-safe query and persistence operations for 3D pose
    estimation records, including creation, primary key lookup, deletion,
    idempotency checks, and dependency resolution for cascade cleanup.

    Attributes
    ----------
    model_class : ClassVar[type[Estimation]]
        SQLAlchemy ORM model class bound to the ensam3d_results table.
        Used for static type checking of all inherited query and
        persistence operations.
    """

    model_class: ClassVar[type[Estimation]] = Estimation

    @classmethod
    async def get_all_by_video_id(
        cls,
        session: AsyncSession,
        video_id: int,
    ) -> list[Estimation]:
        """
        Fetch all pose analysis results associated with a specific video.

        Parameters
        ----------
        session : AsyncSession
            Active async database session bound to the transaction.
        video_id : int
            Primary key of the source video record in the videos table.

        Returns
        -------
        list of Estimation
            List of ORM instances linked to the specified video via
            the video_id foreign key. Returns an empty list if no
            results are found.
        """
        stmt = select(cls.model_class).where(cls.model_class.video_id == video_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def collect_dependent_storage_keys(
        cls,
        session: AsyncSession,
        estimation_id: int,
    ) -> list[str]:
        """
        Collect all storage keys for an estimation and its visualizations.
        Executes a single SQL query using UNION ALL to retrieve storage
        keys from the estimations and visualizations tables based on
        foreign key relationships. Eliminates N+1 query patterns during
        cascade cleanup operations.

        Parameters
        ----------
        session : AsyncSession
            Active async database session bound to the transaction.
        estimation_id : int
            Primary key of the source estimation record.

        Returns
        -------
        list of str
            Flat list of storage keys associated with the estimation and
            all linked visualization records. Returns an empty list if
            the estimation ID does not exist or has no dependents.
        """
        est_q = select(cls.model_class.storage_key).where(
            cls.model_class.id == estimation_id
        )
        vis_q = select(Visualization.storage_key).where(
            Visualization.estimation_id == estimation_id
        )

        stmt = union_all(est_q, vis_q)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]