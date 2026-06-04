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

# packages/server/src/server/modules/estimation/download/routes.py
from fastapi import status, Path, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib.session import get_async_db_session
from minio_lib import StorageOperations
from ..router import estimation_router
from ..utils import get_estimation_or_404


@estimation_router.get(
    "/download/{estimation_id}/",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download estimation file by database ID",
    description="""
        Retrieves estimation metadata by ID, fetches the corresponding
        safetensors archive from object storage, and returns raw bytes
        with proper MIME type and Content-Disposition headers for
        browser download.
    """,
)
async def download_estimation_route(
    estimation_id: int = Path(..., description="Primary key of the target estimation record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> Response:
    """
    Fetch estimation bytes from object storage using the database identifier.

    Parameters
    ----------
    estimation_id : int
        Primary key of the estimation record in the estimations table.
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
        404 Not Found if the estimation ID does not exist in the database
        or the corresponding file is missing in storage.
        500 Internal Server Error if object storage read fails.
    """
    estimation = await get_estimation_or_404(session, estimation_id)
    
    estimation_bytes, content_type = await StorageOperations.download_bytes_with_type(
        estimation.storage_key
    )
    
    filename = estimation.storage_key.split("/")[-1]
    
    return Response(
        content=estimation_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )