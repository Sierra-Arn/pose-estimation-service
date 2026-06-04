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

# packages/server/src/server/exception_handlers/validation.py
import logging
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .schemas import ErrorResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle RequestValidationError and return a standardized ErrorResponse payload.

    Converts Pydantic validation errors raised during request parsing into the
    application's uniform error envelope. Validation failures are logged at warning
    level to distinguish invalid client input from application faults. The primary
    validation message is extracted and included in the detail field to provide a
    concise explanation of the failure.

    Parameters
    ----------
    request : Request
        Incoming FastAPI request object. Provides method and URL context for
        structured log records.
    exc : RequestValidationError
        Raised exception containing the list of Pydantic validation errors.

    Returns
    -------
    JSONResponse
        Formatted error response with 422 status code and standardized JSON
        body containing the primary validation failure message.
    """
    errors = exc.errors()
    logger.warning(
        "Validation error",
        extra={
            "method": request.method,
            "url": str(request.url),
            "errors": errors,
        },
    )

    first_error = errors[0] if errors else {}
    detail = str(first_error.get("ctx", {}).get("error", first_error.get("msg", "Invalid request payload")))

    body = ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error="Unprocessable Entity",
        detail=detail,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=body.model_dump())