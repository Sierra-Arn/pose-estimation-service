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

# app/server/modules/video/download/routes.py
from fastapi import status, Path, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..router import video_router
from ..utils import get_video_or_404
from .....shared.postgres import get_async_db_session
from .....shared.minio import StorageOperations


@video_router.get(
    "/download/{video_id}/",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download video file by database ID",
    description="""
        Retrieves video metadata by ID, fetches the corresponding object 
        from storage, and returns raw bytes.
    """
)
async def download_video_route(
    video_id: int = Path(..., description="Primary key of the target video record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> Response:
    """
    Fetch video bytes from object storage using the database identifier.

    Parameters
    ----------
    video_id : int
        Primary key of the video record in the videos table.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    Response
        Raw binary response with application octet-stream media type.

    Raises
    ------
    HTTPException
        404 Not Found if the video ID does not exist in the database.
        500 Internal Server Error if object storage read fails or the
        file is missing despite a valid database record.
    """
    video = await get_video_or_404(session, video_id)
    video_bytes = await StorageOperations.download_bytes(video.storage_key)
    return Response(content=video_bytes, media_type="application/octet-stream")
