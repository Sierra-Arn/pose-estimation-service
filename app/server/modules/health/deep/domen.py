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

# app/server/modules/health/deep/domen.py
import logging
from sqlalchemy import text
import redis.asyncio as aioredis
from ..types import ServiceStatus
from .....shared.postgres.session import async_engine
from .....shared.redis import redis_config
from .....shared.minio import minio_config, get_async_client
from .....workers.task_queue import celery_config, celery_app

logger = logging.getLogger(__name__)


async def check_minio() -> ServiceStatus:
    """
    Verify MinIO availability by checking the configured bucket.

    Attempts to retrieve bucket metadata using a head request to
    confirm connectivity and access permissions without transferring
    object data or enumerating contents.

    Returns
    -------
    ServiceStatus
        ServiceStatus.OK if the head request succeeds;
        ServiceStatus.UNAVAILABLE if the request times out, fails
        authentication, or returns a client error.
    """
    try:
        async with get_async_client() as client:
            await client.head_bucket(Bucket=minio_config.user_bucket_name)
        return ServiceStatus.OK
    except Exception as e:
        logger.error(
            "MinIO healthcheck failed",
            exc_info=e,
        )
        return ServiceStatus.UNAVAILABLE


async def check_postgres() -> ServiceStatus:
    """
    Verify PostgreSQL availability by executing a lightweight query.

    Opens an asynchronous connection and runs a constant selection
    to confirm the database engine is responsive and accepting
    transactions.

    Returns
    -------
    ServiceStatus
        ServiceStatus.OK if the query executes successfully;
        ServiceStatus.UNAVAILABLE if the connection fails, times
        out, or encounters a database error.
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return ServiceStatus.OK
    except Exception as e:
        logger.error(
            "PostgreSQL healthcheck failed",
            exc_info=e,
        )
        return ServiceStatus.UNAVAILABLE


async def check_redis() -> ServiceStatus:
    """
    Verify Redis availability by establishing a connection and
    issuing a ping command.

    Creates an asynchronous Redis client pointing to the broker
    database index defined in the Celery configuration and sends
    a direct connectivity probe.

    Returns
    -------
    ServiceStatus
        ServiceStatus.OK if the ping returns a successful response;
        ServiceStatus.UNAVAILABLE if the connection is refused,
        times out, or encounters an authentication error.
    """
    try:
        async_redis_client = aioredis.from_url(
            redis_config.connection_url,
            db=celery_config.broker_db_index,
            decode_responses=False,
        )

        await async_redis_client.ping()
        return ServiceStatus.OK
    except Exception as e:
        logger.error(
            "Redis healthcheck failed",
            exc_info=e,
        )
        return ServiceStatus.UNAVAILABLE


def check_celery() -> ServiceStatus:
    """
    Verify Celery worker availability by broadcasting a ping request.

    Uses the Celery control interface to query active workers and
    waits for a response within a two second timeout to confirm at
    least one worker is online and consuming tasks from the broker.

    Returns
    -------
    ServiceStatus
        ServiceStatus.OK if one or more workers acknowledge the ping;
        ServiceStatus.UNAVAILABLE if no workers respond or the control
        request fails.
    """
    try:
        response = celery_app.control.inspect(timeout=2).ping()
        if not response:
            return ServiceStatus.UNAVAILABLE
        return ServiceStatus.OK
    except Exception as e:
        logger.error(
            "Celery healthcheck failed",
            exc_info=e,
        )
        return ServiceStatus.UNAVAILABLE