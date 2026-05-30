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

# app/workers/task_queue/config.py
from typing import ClassVar, Final
from pydantic import Field
from ...shared.base_config import BaseConfig
from ...shared.redis.config import redis_config


class CeleryConfig(BaseConfig):
    """
    Configuration schema for Celery task queue service connectivity.

    Stores connection parameters for accessing a Redis-backed Celery broker
    and result backend. All fields support resolution from environment
    variables prefixed with CELERY_ following the BaseConfig precedence
    rules. The broker_url and result_backend_url properties assemble complete
    Redis URIs with database indices for task routing and result storage.

    Attributes
    ----------
    broker_db_index : int
        Redis database index used for the message broker. Default is 0.
    result_db_index : int
        Redis database index used for storing task results. Default is 1.
    app_name : str
        Human-readable identifier for the Celery application instance.
        Default is "ensam3d-backend".
    result_expires : int
        Time-to-live in seconds for stored task results before automatic
        cleanup. Default is 60.
    queue_name_inference : str
        Queue identifier for routing ML inference and pose estimation tasks.
        Default is "ensam3d".
    queue_name_default : str
        Queue identifier for routing general-purpose background operations.
        Default is "default".
    exchange_name : str
        Name of the shared exchange used for binding task queues and routing
        messages. Default is "tasks".
    broker_url : str
        Read-only property assembling the full Redis broker URI with
        credentials and database index.
    result_backend_url : str
        Read-only property assembling the full Redis result backend URI with
        credentials and database index.
    _task_serializer : str
        Serialization format for task arguments and kwargs passed to workers.
        Default is "json".
    _result_serializer : str
        Serialization format for task return values stored in the result
        backend. Default is "json".
    _accept_content : list of str
        Whitelist of content types the worker will deserialize.
        Default is ["json"].
    _timezone : str
        IANA timezone identifier used for scheduling and timestamp
        serialization. Default is "UTC".
    _enable_utc : bool
        Whether all internal timestamps use UTC. Default is True.
    _exchange_type : str
        Exchange routing strategy for Celery message delivery.
        Default is "direct".
    """

    env_prefix: ClassVar[str] = "CELERY_"

    # ======= ENV-DEPENDENT (configurable via CELERY_ prefixed env vars) =======

    broker_db_index: int = Field(default=0, ge=0)
    result_db_index: int = Field(default=1, ge=0)
    app_name: str = "ensam3d-backend"
    result_expires: int = 60
    queue_name_inference: str = "ensam3d"
    queue_name_default: str = "default"
    exchange_name: str = "tasks"

    # ======= ARCHITECTURAL CONSTANTS (private, not configurable via env) =======

    _task_serializer: Final[str] = "json"
    _result_serializer: Final[str] = "json"
    _accept_content: Final[list[str]] = ["json"]
    _timezone: Final[str] = "UTC"
    _enable_utc: Final[bool] = True
    _exchange_type: Final[str] = "direct"

    @property
    def broker_url(self) -> str:
        """
        Build broker URL for Celery using Redis connection and broker DB index.

        Returns
        -------
        str
            Broker URL in format: redis://username:password@host:port/db_index
        """
        return f"{redis_config.connection_url}/{self.broker_db_index}"

    @property
    def result_backend_url(self) -> str:
        """
        Build result backend URL for Celery using Redis connection and result DB index.

        Returns
        -------
        str
            Result backend URL in format: redis://username:password@host:port/db_index
        """
        return f"{redis_config.connection_url}/{self.result_db_index}"


celery_config = CeleryConfig()