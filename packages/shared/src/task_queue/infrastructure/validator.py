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

# packages/shared/src/task_queue/infrastructure/validator.py
import hashlib
import json
from typing import Any
from postgres_lib import get_sync_db_session
from .types import TaskType, CacheValidationResult, task_config


def validate_task_request(
    params: dict[str, Any],
    task_type: TaskType,
) -> CacheValidationResult:
    """
    Generate deterministic storage key and verify cache existence in PostgreSQL.

    Constructs a canonical JSON representation of task-specific parameters,
    computes its SHA-256 digest, and assembles a deterministic object storage
    key based on the task type. Queries the appropriate repository using
    synchronous I/O to detect idempotent submissions and avoid redundant
    pipeline executions.

    Parameters
    ----------
    params : dict[str, Any]
        Dictionary of task-specific parameters to include in the hash.
        Must be JSON-serializable and contain all fields that affect
        the output artifact. Order does not matter due to sort_keys=True.
    task_type : TaskType
        Domain category of the task. Determines repository, path prefix,
        and file extension via the _TASK_CONFIG mapping.

    Returns
    -------
    CacheValidationResult
        Generic validation container. If is_duplicate is True, id contains
        the existing record primary key and storage_key is None. If False,
        storage_key contains the deterministic MinIO path for the new
        artifact and id is None.

    Notes
    -----
    Task-specific configuration is resolved from _TASK_CONFIG at runtime.
    If task_type is not registered, KeyError is raised immediately to
    prevent silent misconfiguration. The function enforces strict separation
    of concerns: hashing logic is generic, while domain mappings are
    declarative and centralized.
    """
    repository_cls, prefix, extension = task_config[task_type]

    canonical_bytes = json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hash_hex = hashlib.sha256(canonical_bytes).hexdigest()
    storage_key = f"{prefix}{hash_hex}{extension}"

    with get_sync_db_session() as session:
        existing = repository_cls.get_by_storage_key_sync(session, storage_key)

        if existing is not None:
            return CacheValidationResult(
                is_duplicate=True,
                id=existing.id,
                storage_key=None,
            )

        return CacheValidationResult(
            is_duplicate=False,
            id=None,
            storage_key=storage_key,
        )