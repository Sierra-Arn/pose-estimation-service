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

# app/workers/task_infra/types.py
from enum import StrEnum
from typing import TypedDict, NamedTuple
from ...shared.postgres import (
    BaseRepository, 
    EstimationRepository, 
    VisualizationRepository
)


class TaskType(StrEnum):
    """
    Enumeration of background task domain types.

    Defines the standardized category for asynchronous operations
    processed by the Celery worker pool. Each member maps to a
    lowercase string identifier used in task routing, result
    serialization, and API response payloads.

    Attributes
    ----------
    ESTIMATION : TaskType
        Task type for 3D human pose estimation pipeline execution.
    VISUALIZATION : TaskType
        Task type for annotated video rendering and object storage upload.
    """

    ESTIMATION = "estimation"
    VISUALIZATION = "visualization"


class TaskResultPayload(TypedDict):
    """
    Structured payload returned by asynchronous Celery tasks.

    Provides a standardized contract for task results consumed by
    the status polling endpoint and client applications. Enables
    deterministic routing and UI context generation without parsing
    opaque identifiers.

    Attributes
    ----------
    resource_type : TaskType
        Domain category of the completed background operation.
        Used for routing, cache key generation, and client UI labels.
    resource_id : int
        Primary key of the created or updated database record.
        Enables direct linking to detail, download, or visualization endpoints.
    """

    resource_type: TaskType
    resource_id: int


class CacheValidationResult(NamedTuple):
    """
    Generic result container for idempotency and cache validation checks.

    Encapsulates the outcome of a deterministic lookup operation against
    a persistent storage backend. Exactly one of the mutually exclusive
    outcome fields is populated based on whether a matching record was found.

    Attributes
    ----------
    is_duplicate : bool
        True if a record with the computed storage key already exists.
        False if the operation is novel and should proceed to execution.
    id : int or None
        Primary key of the existing database record when is_duplicate is True.
        None when is_duplicate is False, indicating no prior execution.
    storage_key : str or None
        Deterministic object storage path derived from input parameters
        when is_duplicate is False. None when is_duplicate is True, as
        the existing record already references the canonical location.
    """
    is_duplicate: bool
    id: int | None
    storage_key: str | None


task_config: dict[TaskType, tuple[type[BaseRepository], str, str]] = {
    TaskType.ESTIMATION: (EstimationRepository, "estimations/", ".safetensors"),
    TaskType.VISUALIZATION: (VisualizationRepository, "visualizations/", ".mp4"),
}
"""
Task-specific configuration mapping for idempotency validation.

Defines the canonical parameters required to validate, hash, and persist
artifacts for each background task type.
"""