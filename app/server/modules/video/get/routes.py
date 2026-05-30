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

# app/server/modules/video/get/routes.py
from fastapi import status, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..router import video_router
from ..schemas import VideoResponse
from ..utils import get_video_or_404
from .....shared.postgres import get_async_db_session, VideoRepository


@video_router.get(
    "/",
    response_model=list[VideoResponse],
    status_code=status.HTTP_200_OK,
    summary="List videos",
    description="Retrieves a paginated list of video records ordered by primary key.",
)
async def list_videos_route(
    skip: int = Query(0, ge=0, description="Number of records to offset from the beginning."),
    limit: int = Query(50, gt=0, le=100, description="Maximum number of records to return."),
    session: AsyncSession = Depends(get_async_db_session),
) -> list[VideoResponse]:
    """
    Fetch a paginated list of video records.

    Parameters
    ----------
    skip : int
        Offset from the start of the result set.
        Default is 0.
    limit : int
        Maximum number of records to return. Capped at 100.
        Default is 50.
    session : AsyncSession
        Active asynchronous database session bound to the transaction.

    Returns
    -------
    list of VideoResponse
        Ordered list of video payloads matching the pagination window.
        Returns an empty list if no records exist in the specified range.
    """
    videos = await VideoRepository.get_all(session, skip=skip, limit=limit)
    return [VideoResponse.model_validate(v) for v in videos]


@video_router.get(
    "/{video_id}/",
    response_model=VideoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get video details",
    description="Retrieves technical specifications, storage location, and optional label for a specific video record.",
)
async def get_video_route(
    video_id: int = Path(..., description="Primary key of the target video record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> VideoResponse:
    """
    Fetch a single video record by primary key.

    Parameters
    ----------
    video_id : int
        Primary key of the target video in the videos table.
    session : AsyncSession
        Active asynchronous database session bound to the transaction.

    Returns
    -------
    VideoResponse
        Structured payload containing resolution, frame rate, duration,
        storage key, and description.

    Raises
    ------
    HTTPException
        404 Not Found if the video ID does not exist in the database.
    """
    video = await get_video_or_404(session, video_id)
    return VideoResponse.model_validate(video)