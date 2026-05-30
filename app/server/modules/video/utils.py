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

# app/server/modules/video/utils.py
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....shared.postgres import Video, VideoRepository


async def get_video_or_404(
    session: AsyncSession,
    video_id: int,
) -> Video:
    """
    Fetch a video record by primary key or raise a 404 HTTP exception.

    Utility function to consolidate the common pattern of looking up a
    video by its database identifier and returning a standardized
    Not Found response when the record does not exist.

    Parameters
    ----------
    session : AsyncSession
        Active async database session bound to the current transaction.
    video_id : int
        Primary key of the target video record in the videos table.

    Returns
    -------
    Video
        ORM instance of the requested video record.

    Raises
    ------
    HTTPException
        404 Not Found with a standardized detail message if the video
        ID does not exist in the database.
    """
    video = await VideoRepository.get_by_id(session, video_id)
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video record not found in the database.",
        )
    return video