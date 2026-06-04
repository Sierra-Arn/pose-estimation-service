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

# packages/server/src/server/exception_handlers/http.py
import logging
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from http import HTTPStatus
from .schemas import ErrorResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException and return a standardized ErrorResponse payload.

    Maps the exception status code to its canonical HTTP phrase and
    packages it with the exception detail into a uniform error envelope.
    Client errors in the 4xx range are logged at warning level to
    distinguish invalid requests from application faults. Server errors
    in the 5xx range are logged at error level to signal internal
    failures requiring investigation.

    Parameters
    ----------
    request : Request
        Incoming FastAPI request object. Provides method and URL
        context for structured log records.
    exc : HTTPException
        Raised exception containing the HTTP status code and detail
        message.

    Returns
    -------
    JSONResponse
        Formatted error response with matching status code and
        standardized JSON body.
    """
    phrase = HTTPStatus(exc.status_code).phrase
    log_extra = {
        "method": request.method,
        "url": str(request.url),
        "status_code": exc.status_code,
        "detail": exc.detail,
    }

    if exc.status_code >= 500:
        logger.error("HTTP error", extra=log_extra)
    else:
        logger.warning("HTTP error", extra=log_extra)

    body = ErrorResponse(
        status_code=exc.status_code,
        error=phrase,
        detail=exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())