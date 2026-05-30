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

# app/server/modules/health/types.py
from enum import StrEnum


class ServiceStatus(StrEnum):
    """
    Enumeration of service health states for runtime availability reporting.

    Represents the operational status of the application and its external
    dependencies as observed during health checks. Used to drive readiness
    and liveness probes in container orchestration environments.

    Attributes
    ----------
    OK : ServiceStatus
        All critical components are reachable and responding within expected
        thresholds; the service is fully operational.
    DEGRADED : ServiceStatus
        Core application logic is functional but one or more non-critical
        dependencies are unavailable; partial feature set may be affected.
    UNAVAILABLE : ServiceStatus
        The service failed to respond to health probes or critical dependencies
        are unreachable; the instance should not receive production traffic.
    """

    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"