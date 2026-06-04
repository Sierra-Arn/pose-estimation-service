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

# packages/server/src/server/modules/health/shallow/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from ..types import ServiceStatus


class ShallowHealthResponse(BaseModel):
    """
    Response body for shallow health check endpoint.

    Represents the minimal availability signal exposed by the application
    to load balancers and orchestration probes. Contains only the aggregate
    service status without dependency details or diagnostic metadata.
    """

    status: ServiceStatus = Field(
        description="Overall application status. ok if the application is running and accepting requests.",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                }
            ]
        },
    )