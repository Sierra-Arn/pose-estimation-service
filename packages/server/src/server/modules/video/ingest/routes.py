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

# packages/server/src/server/modules/video/ingest/routes.py
import asyncio
from fastapi import UploadFile, File, HTTPException, status, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session, Video
from minio_lib import StorageOperations
from .domen import validate_video_upload
from ..router import video_router
from ..schemas import VideoResponse


@video_router.post(
    "/ingest/",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new video",
    description="""
        Accepts a video file, validates content, extracts metadata, uploads to object storage, 
        and registers the asset. Returns complete metadata for newly created or duplicate records.
    """
)
async def ingest_video_route(
    file: UploadFile = File(...),
    description: str | None = Form(None),
    session: AsyncSession = Depends(get_async_db_session),
) -> VideoResponse:
    """
    Handle multipart video ingestion with content-based deduplication.

    Parameters
    ----------
    file : UploadFile
        Uploaded video file from the client request.
    description : str or None, optional
        Optional textual description for the video asset. Default is None.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    VideoResponse
        Canonical representation of the ingested video asset. Contains the
        database identifier, object storage location, resolution, frame rate,
        duration, MIME content type, and optional description. Returned for
        both newly created records and duplicate content that matched an
        existing hash.

    Raises
    ------
    HTTPException
        400 Bad Request if the file is empty, its detected MIME type is
        unsupported, or required metadata cannot be extracted.
        500 Internal Server Error if object storage or database operations fail.
    """
    video_bytes = await file.read()
    if not video_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        validation_result = await asyncio.to_thread(validate_video_upload, video_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze uploaded file: {exc}",
        ) from exc

    if validation_result.is_duplicate:
        return VideoResponse.model_validate(validation_result.video)

    try:
        await StorageOperations.upload_bytes(
            storage_key=validation_result.storage_key,
            data=video_bytes,
            content_type=validation_result.content_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to object storage: {exc}",
        ) from exc

    try:
        new_video = Video(
            storage_key=validation_result.storage_key,
            width=validation_result.metadata.width,
            height=validation_result.metadata.height,
            fps=validation_result.metadata.fps,
            duration_seconds=validation_result.metadata.duration_seconds,
            description=description,
        )
        session.add(new_video)
        await session.flush()
        await session.refresh(new_video)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        await StorageOperations.delete(validation_result.storage_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database registration failed: {exc}",
        ) from exc

    return VideoResponse.model_validate(new_video)