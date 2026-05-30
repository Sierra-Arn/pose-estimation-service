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

# app/server/modules/health/deep/routes.py
import asyncio
from fastapi import status
from .schemas import DeepHealthResponse
from .domen import (
    check_postgres, 
    check_redis, 
    check_minio, 
    check_celery
)
from ..router import health_router
from ....config import server_config
from ..types import ServiceStatus


@health_router.get(
    "/deep/",
    status_code=status.HTTP_200_OK,
    response_model=DeepHealthResponse,
    summary="Deep Health check",
    description=("""
        Returns the availability status of the application and its dependencies. 
        Each field indicates whether the corresponding service is reachable or unreachable.
    """)
)
async def deep_health_route() -> DeepHealthResponse:
    """
    Execute concurrent health probes for all external dependencies.

    Runs PostgreSQL, Redis, MinIO, and Celery checks in parallel.
    Celery inspection is synchronous and executed in a worker thread
    to avoid blocking the event loop. All probes must complete within
    three seconds. On timeout the endpoint returns unavailable to
    signal orchestrators that the instance cannot serve traffic safely.
    """
    try:
        postgres, redis, minio, celery = await asyncio.wait_for(
            asyncio.gather(
                check_postgres(),
                check_redis(),
                check_minio(),
                asyncio.to_thread(check_celery),
            ),
            timeout=server_config.deep_health_timeout,
        )
    except asyncio.TimeoutError:
        return DeepHealthResponse(
            status=ServiceStatus.UNAVAILABLE,
            postgres=ServiceStatus.UNAVAILABLE,
            redis=ServiceStatus.UNAVAILABLE,
            minio=ServiceStatus.UNAVAILABLE,
            celery=ServiceStatus.UNAVAILABLE,
        )

    overall = (
        ServiceStatus.OK
        if all(s == ServiceStatus.OK for s in (postgres, redis, minio, celery))
        else ServiceStatus.DEGRADED
    )

    return DeepHealthResponse(
        status=overall,
        postgres=postgres,
        redis=redis,
        minio=minio,
        celery=celery,
    )