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

# packages/server/src/server/modules/task/routes.py
from fastapi import APIRouter, status, HTTPException, Path
from celery.result import AsyncResult
from task_queue import celery_app
from .schemas import TaskResponse

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get(
    "/{task_id}/",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Check background task status",
    description="Retrieves the current execution state and result payload of a submitted Celery task.",
)
async def get_task_status_route(
    task_id: str = Path(..., description="Celery task identifier returned upon task submission."),
) -> TaskResponse:
    """
    Query Celery result backend for the current state of an asynchronous task.

    Parameters
    ----------
    task_id : str
        Celery task identifier to inspect.

    Returns
    -------
    TaskResponse
        Structured response containing the task identifier, current execution
        state, and optional result payload. Valid status values include
        PENDING, STARTED, SUCCESS, FAILURE, RETRY, and REVOKED. The result
        field is populated only when status equals SUCCESS.

    Raises
    ------
    HTTPException
        500 Internal Server Error if the Celery result backend is
        unreachable or returns malformed state data.
    """

    try:
        task_result = AsyncResult(task_id, app=celery_app)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query task backend: {exc}",
        ) from exc

    status_str = task_result.status

    if status_str == "SUCCESS":
        payload = task_result.result
    else:
        payload = None

    return TaskResponse(
        task_id=task_id,
        status=status_str,
        result=payload,
    )