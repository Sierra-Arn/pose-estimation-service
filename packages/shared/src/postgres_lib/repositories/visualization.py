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

# packages/shared/src/postgres_lib/repositories/visualization.py
from typing import ClassVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Visualization
from .base import BaseRepository


class VisualizationRepository(BaseRepository):
    """
    Stateless data access implementation for the Visualization ORM model.
    
    Provides type-safe query and persistence operations for rendered pose
    visualization records, including creation, primary key lookup, deletion,
    and storage key validation.

    Attributes
    ----------
    model_class : ClassVar[type[Visualization]]
        SQLAlchemy ORM model class bound to the visualizations table.
        Used for static type checking of all inherited query and
        persistence operations.
    """

    model_class: ClassVar[type[Visualization]] = Visualization

    @classmethod
    async def get_all_by_estimation_id(
        cls,
        session: AsyncSession,
        estimation_id: int,
    ) -> list[Visualization]:
        """
        Fetch all visualization renders associated with a specific pose analysis result.

        Parameters
        ----------
        session : AsyncSession
            Active async database session bound to the transaction.
        estimation_id : int
            Primary key of the source pose analysis record in the
            estimations table.

        Returns
        -------
        list of Visualization
            List of ORM instances linked to the specified result via
            the estimation_id foreign key. Returns an empty list if no
            visualizations are found.
        """
        stmt = select(cls.model_class).where(cls.model_class.estimation_id == estimation_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())
