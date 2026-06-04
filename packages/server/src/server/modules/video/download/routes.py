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

# packages/server/src/server/modules/video/download/routes.py
from fastapi import status, Path, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session
from minio_lib import StorageOperations
from ..router import video_router
from ..utils import get_video_or_404


@video_router.get(
    "/download/{video_id}/",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download video file by database ID",
    description="""
        Retrieves video metadata by ID, fetches the corresponding object 
        from storage, and returns raw bytes with proper MIME type and
        Content-Disposition headers for browser download.
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
        Binary response with the MIME content type from object storage
        metadata and Content-Disposition header containing the original
        filename for browser download prompts.

    Raises
    ------
    HTTPException
        404 Not Found if the video ID does not exist in the database.
        500 Internal Server Error if object storage read fails or the
        file is missing despite a valid database record.
    """
    video = await get_video_or_404(session, video_id)
    
    video_bytes, content_type = await StorageOperations.download_bytes_with_type(
        video.storage_key
    )
    
    filename = video.storage_key.split("/")[-1]
    
    return Response(
        content=video_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )