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

# app/workers/default/config.py
from typing import ClassVar, Literal
from pydantic import Field
from ...shared.base_config import BaseConfig
from ...shared.logger import LogLevel


class DefaultWorkerConfig(BaseConfig):
    """
    Configuration schema for the default Celery worker process.

    Combines environment-supplied parameters controlling worker identity,
    execution pool strategy, concurrency, and logging verbosity. Unlike the
    inference worker, all operational parameters are configurable at launch
    time since the default worker handles CPU-bound background operations
    without GPU memory constraints.

    Attributes
    ----------
    name : str
        Worker identity string used for routing and monitoring. Appears in
        Celery logs and worker lists. Default is "default_worker@%n" where
        %n is expanded by Celery to the hostname at worker startup.
    pool : Literal["prefork", "solo"]
        Celery worker pool implementation. prefork uses multiple processes
        for CPU-bound workloads; solo runs tasks sequentially in a single
        process for debugging or resource-constrained environments.
        Default is "prefork".
    concurrency : int
        Number of parallel worker processes or threads. For prefork pool
        this sets the process count. Ignored when pool is solo.
        Default is 4.
    prefetch_multiplier : int
        Number of tasks fetched from the broker ahead of execution. Higher
        values increase throughput but may cause task starvation across
        workers. Default is 1.
    log_level : LogLevel
        Minimum severity threshold for log message processing. Controls
        verbosity of worker lifecycle events and task execution diagnostics.
        Default is "INFO".
    """

    env_prefix: ClassVar[str] = "WORKER_DEFAULT_"

    # === ENV-DEPENDENT (configurable via WORKER_DEFAULT_ prefixed env vars) ===
    name: str = "default_worker@%n"
    pool: Literal["prefork", "solo"] = "prefork"
    concurrency: int = Field(default=4, ge=1)
    prefetch_multiplier: int = Field(default=1, ge=1)
    log_level: LogLevel = "INFO"


default_worker_config = DefaultWorkerConfig()