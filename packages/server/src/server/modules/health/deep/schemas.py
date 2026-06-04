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

# packages/server/src/server/modules/health/deep/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from ..types import ServiceStatus
 
 
class DeepHealthResponse(BaseModel):
    """
    Response body for deep health check endpoint.

    Reports the operational status of the application and its external
    dependencies, including object storage, database, message broker,
    and cache. Used for comprehensive readiness probes and diagnostic
    dashboards.
    """

    status: ServiceStatus = Field(
        description="""
            Overall application status derived from dependency states. 
            Returns ok when all critical services are reachable; 
            degraded when one or more are unavailable.
        """
    )

    minio: ServiceStatus = Field(
        description="MinIO object storage availability. ok if bucket access succeeds; unavailable otherwise."
    )

    postgres: ServiceStatus = Field(
        description="PostgreSQL availability. ok if a test query succeeds; unavailable otherwise."
    )

    redis: ServiceStatus = Field(
        description="Redis availability. ok if a PING command succeeds; unavailable otherwise."
    )

    celery: ServiceStatus = Field(
        description="""
            Celery task broker availability. 
            ok if the broker connection responds to health probes; 
            unavailable otherwise.
        """
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "minio": "ok",
                    "postgres": "ok",
                    "redis": "ok",
                    "celery": "ok",
                }
            ]
        },
    )