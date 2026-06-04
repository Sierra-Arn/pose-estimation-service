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

# packages/server/src/server/modules/estimation/delete/routes.py
from fastapi import HTTPException, status, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session, EstimationRepository
from minio_lib import StorageOperations
from ..router import estimation_router
from ..utils import get_estimation_or_404


@estimation_router.delete(
    "/{estimation_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete estimation and all related artifacts",
    description="""
        Removes the estimation record, all associated visualization outputs, 
        and their corresponding files from object storage.
    """
)
async def delete_estimation_route(
    estimation_id: int = Path(..., description="Primary key of the target estimation record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> None:
    """
    Delete an estimation record and cascade-remove all dependent visualization data.

    Parameters
    ----------
    estimation_id : int
        Primary key of the estimation record in the estimations table.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    None
        Returns 204 No Content on successful deletion.

    Raises
    ------
    HTTPException
        404 Not Found if the estimation ID does not exist in the database.
        500 Internal Server Error if object storage cleanup or database deletion fails.
    """
    estimation = await get_estimation_or_404(session, estimation_id)
    storage_keys = await EstimationRepository.collect_dependent_storage_keys(session, estimation_id)

    if storage_keys:
        try:
            await StorageOperations.delete_objects_batch(storage_keys)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clean up object storage: {exc}",
            ) from exc

    try:
        await session.delete(estimation)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database deletion failed: {exc}",
        ) from exc