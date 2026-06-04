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

# packages/server/src/server/modules/video/delete/routes.py
from fastapi import status, Path, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session, VideoRepository
from minio_lib import StorageOperations
from ..router import video_router
from ..utils import get_video_or_404


@video_router.delete(
    "/{video_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete video and all related artifacts",
    description="""
        Removes the video record, all associated estimation results, 
        visualization outputs, and their corresponding files from object storage.
    """
)
async def delete_video_route(
    video_id: int = Path(..., description="Primary key of the target video record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> None:
    """
    Delete a video record and cascade-remove all dependent analysis and visualization data.

    Parameters
    ----------
    video_id : int
        Primary key of the video record in the videos table.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    None
        Returns 204 No Content on successful deletion.

    Raises
    ------
    HTTPException
        404 Not Found if the video ID does not exist in the database.
        500 Internal Server Error if object storage cleanup or database deletion fails.
    """
    video = await get_video_or_404(session, video_id)
    storage_keys = await VideoRepository.collect_dependent_storage_keys(session, video_id)

    if storage_keys:
        try:
            await StorageOperations.delete_objects_batch(storage_keys)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clean up object storage: {exc}",
            ) from exc

    try:
        await session.delete(video)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database deletion failed: {exc}",
        ) from exc