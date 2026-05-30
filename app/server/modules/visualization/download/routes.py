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

# app/server/modules/visualization/download/routes.py
from fastapi import status, Path, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from ..router import visualization_router
from ..utils import get_visualization_or_404
from .....shared.postgres import get_async_db_session
from .....shared.minio import StorageOperations


@visualization_router.get(
    "/download/{visualization_id}/",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download visualization video",
    description="""
        Retrieves visualization metadata by ID, fetches the corresponding video 
        file from object storage, and returns raw bytes.
    """    
)
async def download_visualization_route(
    visualization_id: int = Path(..., description="Primary key of the target visualization record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> Response:
    """
    Fetch visualization video bytes from object storage using the database identifier.

    Parameters
    ----------
    visualization_id : int
        Primary key of the visualization record in the visualizations table.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    Response
        Raw binary response with application octet-stream media type.

    Raises
    ------
    HTTPException
        404 Not Found if the visualization ID does not exist in the database
        or the corresponding file is missing in storage.
        500 Internal Server Error if object storage read fails.
    """
    visualization = await get_visualization_or_404(session, visualization_id)
    video_bytes = await StorageOperations.download_bytes(visualization.storage_key)
    return Response(content=video_bytes, media_type="application/octet-stream")
