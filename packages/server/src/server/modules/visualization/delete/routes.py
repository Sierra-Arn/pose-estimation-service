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

# packages/server/src/server/modules/visualization/delete/routes.py
from fastapi import HTTPException, status, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session
from minio_lib import StorageOperations
from ..router import visualization_router
from ..utils import get_visualization_or_404


@visualization_router.delete(
    "/{visualization_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete visualization record and video file",
    description="""
        Removes the visualization metadata record from the database and deletes 
        the corresponding video from object storage.
    """
)
async def delete_visualization_route(
    visualization_id: int = Path(..., description="Primary key of the target visualization record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> None:
    """
    Delete a visualization record and its associated video file from storage.

    Parameters
    ----------
    visualization_id : int
        Primary key of the visualization record in the visualizations table.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    None
        Returns 204 No Content on successful deletion.

    Raises
    ------
    HTTPException
        404 Not Found if the visualization ID does not exist in the database.
        500 Internal Server Error if object storage cleanup or database deletion fails.
    """
    visualization = await get_visualization_or_404(session, visualization_id)

    try:
        await StorageOperations.delete(visualization.storage_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clean up object storage: {exc}",
        ) from exc

    try:
        await session.delete(visualization)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database deletion failed: {exc}",
        ) from exc