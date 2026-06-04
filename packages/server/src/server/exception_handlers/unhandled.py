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

# packages/server/src/server/exception_handlers/unhandled.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from .schemas import ErrorResponse

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for uncaught exceptions falling through specific error routes.

    Records the complete traceback at error level with request context for
    post-mortem diagnostics. Returns a standardized error payload with a
    500 status code to prevent leaking internal implementation details
    to the client.

    Parameters
    ----------
    request : Request
        Incoming FastAPI request object. Provides method and URL
        context for structured log records.
    exc : Exception
        Uncaught exception that triggered the handler.

    Returns
    -------
    JSONResponse
        Formatted error response with 500 status code and
        standardized JSON body.
    """
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "method": request.method,
            "url": str(request.url),
        },
    )
    body = ErrorResponse(
        status_code=500,
        error="Internal Server Error",
        detail="Internal server error",
    )
    return JSONResponse(status_code=500, content=body.model_dump())