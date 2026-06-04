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

# packages/server/src/server/exception_handlers/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """
    Uniform error response body returned for all handled exceptions.

    The status_code field intentionally mirrors the HTTP response status code.
    Although the code is already present in the response headers, including it
    in the body makes the payload self-contained: clients that log or forward
    only the JSON body retain the full context without needing to inspect
    headers separately.
    """

    status_code: int = Field(
        description="HTTP status code of the response (e.g., 404, 422, 500).",
    )
    error: str = Field(
        description=(
            "Short human-readable name for the error, derived from the HTTP "
            "status phrase (e.g., 'Not Found', 'Unprocessable Entity')."
        )
    )
    detail: str = Field(
        description=(
            "Specific description of what went wrong. Should be informative "
            "enough for the client to understand the cause without exposing "
            "internal implementation details."
        )
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "status_code": 404,
                    "error": "Not Found",
                    "detail": "User with id 42 does not exist",
                }
            ]
        }
    )


