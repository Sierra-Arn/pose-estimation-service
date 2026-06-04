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

# packages/server/src/server/app.py
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from .config import server_config
from .exception_handlers import (
    validation_exception_handler, 
    http_exception_handler, 
    unhandled_exception_handler
)
from .modules import (
    health_router, 
    tasks_router,
    video_router, 
    estimation_router, 
    visualization_router
)


def create_app() -> FastAPI:
    """
    Factory function for initializing the FastAPI application instance.

    Configures OpenAPI metadata from shared settings, registers all module
    routers, and attaches a standardized exception handling chain. Validation
    errors, expected HTTP exceptions, and unexpected runtime failures are routed
    to dedicated handlers that enforce a uniform JSON error envelope. The function
    returns a fully configured application ready for ASGI deployment.

    Returns
    -------
    FastAPI
        Configured application instance with routers and global exception
        handlers bound.
    """

    app = FastAPI(
        title=server_config.title,
        description=server_config.description,
        version=server_config.version,
        docs_url=server_config.docs_url,
        redoc_url=server_config.redoc_url,
        openapi_url=server_config.openapi_url,
    )

    app.include_router(health_router)
    app.include_router(tasks_router)
    app.include_router(video_router)
    app.include_router(estimation_router)
    app.include_router(visualization_router)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    return app