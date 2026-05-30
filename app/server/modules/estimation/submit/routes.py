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

# app/server/modules/estimation/submit/routes.py
from fastapi import status, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import EstimationSubmitRequest
from ..router import estimation_router
from ...task.schemas import TaskResponse
from ...video.utils import get_video_or_404
from .....shared.postgres import get_async_db_session
from .....workers.inference.tasks.estimate import estimate_task


@estimation_router.post(
    "/submit/",
    tags=["tasks", "estimations"],
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit estimation task",
    description="""
        Validates the source video record and submits the 3D pose estimation pipeline to the 
        distributed task queue. Idempotency checks and deterministic storage key generation 
        are executed within the Celery worker.
    """
)
async def submit_estimation_route(
    request: EstimationSubmitRequest = Body(...),
    session: AsyncSession = Depends(get_async_db_session),
) -> TaskResponse:
    """
    Verify video existence and enqueue asynchronous estimation task.

    Parameters
    ----------
    request : EstimationSubmitRequest
        Preprocessing and inference parameters for the pipeline.
    session : AsyncSession
        Injected asynchronous database session for the current transaction.

    Returns
    -------
    TaskResponse
        Structured payload containing the Celery task identifier,
        PENDING status, and null result payload for immediate
        asynchronous status polling.

    Raises
    ------
    HTTPException
        404 Not Found if the video record does not exist in the database.
        500 Internal Server Error if task submission to the broker fails.
    """
    video = await get_video_or_404(session, request.video_id)

    try:
        async_result = estimate_task.delay(
            source_storage_key=video.storage_key,
            video_id=request.video_id,
            target_width=request.target_width,
            target_height=request.target_height,
            target_fps=request.target_fps,
            skip_start_seconds=request.skip_start_seconds,
            duration_seconds=request.duration_seconds,
            batch_size=request.batch_size,
            description=request.description,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit estimation task to the broker.",
        ) from exc

    return TaskResponse(
        task_id=async_result.id,
        status="PENDING",
        result=None,
    )