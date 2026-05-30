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

# app/shared/postgres/repositories/base.py
from typing import Any, ClassVar
from abc import ABC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from .types import ModelType


class BaseRepository(ABC):
    """
    Abstract namespace for stateless SQLAlchemy data access operations.

    Enforces that concrete subclasses must define a model_class attribute
    and prohibits direct instantiation of the base class. All data access
    methods are implemented as classmethods to maintain a functional,
    connection-agnostic API surface. Supports both asynchronous and
    synchronous execution contexts where required by the caller.

    Attributes
    ----------
    model_class : ClassVar[type[ModelType]]
        SQLAlchemy ORM model class managed by the repository, bounded by
        Base. Must be explicitly overridden in each concrete subclass with
        a concrete model type to enable strict static type checking for
        query and persistence operations.

    Notes
    -----
    All inherited classmethods are asynchronous by default and expect an
    AsyncSession instance. Synchronous variants are explicitly suffixed
    with _sync and require a standard Session to prevent event loop
    conflicts in background workers.
    """

    model_class: ClassVar[type[ModelType]]

    def __new__(cls, *args, **kwargs) -> None:
        """
        Prevent direct instantiation of BaseRepository.

        Raises
        ------
        TypeError
            Always raised when attempting to instantiate BaseRepository
            directly. Subclasses remain instantiable but are intended
            to be used via classmethods only.
        """
        raise TypeError(
            f"{cls.__name__} cannot be instantiated. "
            "Use classmethods directly on the subclass."
        )

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Validate subclass configuration at definition time.

        Ensures that every concrete repository subclass explicitly
        defines the model_class attribute before the class is created.

        Raises
        ------
        TypeError
            Raised when model_class is missing from the subclass definition.
        """
        super().__init_subclass__(**kwargs)
        if "model_class" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must define 'model_class' as a class variable"
            )

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        obj_data: dict[str, Any],
    ) -> ModelType:
        """
        Create a new record in the database.

        Parameters
        ----------
        session : AsyncSession
            Active async database session bound to the transaction.
        obj_data : dict[str, Any]
            Dictionary of field values matching the ORM model schema.

        Returns
        -------
        ModelType
            Newly created ORM instance with populated id and
            server-generated fields such as created_at.
        """
        db_obj = cls.model_class(**obj_data)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        obj_id: int,
    ) -> ModelType | None:
        """
        Fetch a record by its primary key.

        Parameters
        ----------
        session : AsyncSession
            Active async database session.
        obj_id : int
            Primary key value to look up.

        Returns
        -------
        ModelType or None
            Matching ORM instance, or None if not found.
        """
        stmt = select(cls.model_class).where(cls.model_class.id == obj_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def delete_by_id(
        cls,
        session: AsyncSession,
        obj_id: int,
    ) -> bool:
        """
        Delete a record by its primary key.

        Parameters
        ----------
        session : AsyncSession
            Active async database session.
        obj_id : int
            Primary key of the record to delete.

        Returns
        -------
        bool
            True if a record was found and deleted, False otherwise.
        """
        db_obj = await cls.get_by_id(session, obj_id)
        if db_obj is None:
            return False
        await session.delete(db_obj)
        return True

    @classmethod
    async def get_all(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Fetch a paginated list of records ordered by primary key.

        Parameters
        ----------
        session : AsyncSession
            Active async database session bound to the transaction.
        skip : int, optional
            Number of records to offset from the beginning of the
            result set. Default is 0.
        limit : int, optional
            Maximum number of records to return. Default is 100.

        Returns
        -------
        list of ModelType
            List of ORM instances matching the query, ordered by
            ascending primary key. Returns an empty list if no
            records match the pagination window.
        """
        stmt = (
            select(cls.model_class)
            .order_by(cls.model_class.id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    def get_by_storage_key_sync(
        cls,
        session: Session,
        storage_key: str,
    ) -> ModelType | None:
        """
        Fetch a record by its object storage key using synchronous I/O.

        Parameters
        ----------
        session : Session
            Active synchronous database session bound to the transaction.
        storage_key : str
            Object storage path or identifier for the file artifact.

        Returns
        -------
        ModelType or None
            Matching ORM instance, or None if not found.
        """
        stmt = select(cls.model_class).where(cls.model_class.storage_key == storage_key)
        result = session.execute(stmt)
        return result.scalar_one_or_none()