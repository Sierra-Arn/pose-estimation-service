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

# app/server/modules/tasks/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class TaskResponse(BaseModel):
    """
    Unified response body for background task operations.
    
    Serves as the canonical contract for both task submission and
    status polling endpoints. Provides consistent JSON structure
    across the lifecycle of a Celery background operation.

    Attributes
    ----------
    task_id : str
        Unique identifier of the submitted background task. Used for
        subsequent status polling and result retrieval.
    status : str
        Current execution state of the task. Returns PENDING
        immediately upon submission and updates to STARTED, SUCCESS,
        or FAILURE during polling.
    result : dict or None
        Task result payload if completed successfully. None for
        PENDING, STARTED, or FAILURE states.
    """

    task_id: str = Field(
        ...,
        description="Unique identifier of the submitted background task.",
    )
    status: str = Field(
        ...,
        description="Current execution state of the task.",
    )
    result: dict | None = Field(
        None,
        description="Task result if completed successfully, None otherwise.",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "task_id": "a1b2c3d4-e5f6-4789-90ab-cdef12345678",
                    "status": "PENDING",
                    "result": None,
                }
            ]
        },
    )