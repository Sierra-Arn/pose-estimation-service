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

# packages/server/src/server/config.py
from typing import ClassVar
from pydantic import Field
from base_lib import BaseConfig, LogLevel


class ServerConfig(BaseConfig):
    """
    Configuration schema for the FastAPI server runtime.

    Stores server binding parameters, OpenAPI metadata, documentation
    endpoint paths, and logging thresholds. All fields support resolution
    from environment variables prefixed with SERVER_ following the
    BaseConfig precedence rules.

    Attributes
    ----------
    host : str
        Network interface address for the server to bind. Use "0.0.0.0"
        to accept connections from any interface or "127.0.0.1" for
        localhost only. Default is "0.0.0.0".
    port : int
        TCP port for incoming HTTP requests. Validated to lie within the
        standard 16-bit range. Default is 8000.
    log_level : LogLevel
        Minimum severity threshold for all server-process logs.
        Default is LogLevel.INFO.
    title : str
        Human-readable service name displayed in the generated OpenAPI
        schema and documentation interfaces. Default is
        "Human Pose Estimation Service".
    description : str
        Service overview rendered in the documentation UI describing
        purpose, scope, and key features. Default is the canonical 
        project description.
    version : str
        Semantic version string identifying the current API release.
        Default is "0.1.0".
    docs_url : str or None
        Path to the Swagger UI interface. Set to None to disable
        interactive documentation. Default is "/docs".
    redoc_url : str or None
        Path to the ReDoc interface. Set to None to disable alternative
        documentation rendering. Default is "/redoc".
    openapi_url : str or None
        Path to the raw OpenAPI JSON schema. Disabling this implicitly
        disables both documentation endpoints since they depend on the
        schema payload. Default is "/openapi.json".
    deep_health_timeout : float
        Maximum time in seconds allowed for the deep health check to
        complete all dependency probes before returning unavailable.
        Controls the asyncio wait_for deadline applied to concurrent
        database, cache, storage, and broker checks. Default is 3.0.
    """

    env_prefix: ClassVar[str] = "SERVER_"

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: LogLevel = LogLevel.INFO

    title: str = "Human Pose Estimation Service"
    description: str = (
        "Production-oriented REST API service exposing ensam3d_inference as a managed backend "
        "for distributed 3D human pose estimation, with video ingestion, GPU worker orchestration, "
        "annotated visualization rendering, and persistent artifact storage. "
    )
    version: str = "0.1.0"
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"

    deep_health_timeout: float = 3.0


server_config = ServerConfig()