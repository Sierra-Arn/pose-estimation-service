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

# app/server/modules/visualization/submit/routes.py
from fastapi import status, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import VisualizationSubmitRequest
from ..router import visualization_router
from ...video.utils import get_video_or_404
from ...task.schemas import TaskResponse
from ...estimation.utils import get_estimation_or_404
from .....shared.postgres import get_async_db_session
from .....workers.default.tasks.visualize import visualize_task


@visualization_router.post(
    "/submit/",
    tags=["tasks", "visualizations"],
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit visualization task",
    description="""
        Validates the source estimation record and submits the annotated video
        rendering pipeline to the distributed task queue. Idempotency checks
        and deterministic storage key generation are executed within the Celery worker.
    """,
)
async def submit_visualization_route(
    request: VisualizationSubmitRequest = Body(...),
    session: AsyncSession = Depends(get_async_db_session),
) -> TaskResponse:
    """
    Verify estimation existence and enqueue asynchronous visualization task.

    Parameters
    ----------
    request : VisualizationSubmitRequest
        Overlay configuration and encoding parameters for rendering.
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
        404 Not Found if the estimation or source video record does
        not exist in the database.
        500 Internal Server Error if task submission to the broker fails.
    """
    estimation = await get_estimation_or_404(session, request.estimation_id)
    video = await get_video_or_404(session, estimation.video_id)

    try:
        async_result = visualize_task.delay(
            estimation_id=request.estimation_id,
            source_video_key=video.storage_key,
            safetensors_key=estimation.storage_key,
            target_width=estimation.requested_width,
            target_height=estimation.requested_height,
            target_fps=estimation.requested_fps,
            skip_start_seconds=estimation.skip_start_seconds,
            duration_seconds=estimation.duration_seconds,
            show_bbox=request.show_bbox,
            show_bbox_confidence=request.show_bbox_confidence,
            show_keypoints=request.show_keypoints,
            show_skeleton=request.show_skeleton,
            crf=request.crf,
            preset=request.preset,
            batch_size=request.batch_size,
            description=request.description,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit visualization task to the broker.",
        ) from exc

    return TaskResponse(
        task_id=async_result.id,
        status="PENDING",
        result=None,
    )
