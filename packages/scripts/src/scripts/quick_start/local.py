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

# packages/scripts/src/scripts/quick_start/local.py
"""
Local development environment quick-start script.

This script automates the full bootstrap process for running the application
locally. It sequentially generates configuration files, spins up the Docker
infrastructure, applies database migrations, and launches the API server
along with its background workers in separate terminal windows.

Upon successful startup, the script polls the server's health endpoint and
automatically opens the Swagger UI in the default browser.

Execution sequence:

+------+--------------------------+--------------------------------------------------------------+
| Step | Command                  | Description                                                  |
+======+==========================+==============================================================+
| 1    | ``just gen-env``         | Copies ``config/.env.local.example`` to ``.env`` in the      |
|      |                          | project root and generates cryptographically secure random   |
|      |                          | passwords for all credential fields. Skipped if ``.env``     |
|      |                          | already exists.                                              |
+------+--------------------------+--------------------------------------------------------------+
| 2    | ``just gen-acl``         | Generates ``docker/redis/init/01-create-users.acl`` from     |
|      |                          | environment variables. Defines Redis users with scoped       |
|      |                          | permissions for the application.                             |
+------+--------------------------+--------------------------------------------------------------+
| 3    | ``just gen-sql``         | Generates ``docker/postgres/init/01-create-user.sql`` from   |
|      |                          | environment variables. Creates the application database      |
|      |                          | user with the minimum required privileges.                   |
+------+--------------------------+--------------------------------------------------------------+
| 4    | ``just gen-minio``       | Generates ``docker/minio/init/policy.json`` and              |
|      |                          | ``docker/minio/init/setup.sh`` from environment variables.   |
|      |                          | Defines the bucket access policy and the MinIO               |
|      |                          | initialization script that runs inside the init container.   |
+------+--------------------------+--------------------------------------------------------------+
| 5    | ``just docker-local-up`` | Starts the infrastructure-only Docker Compose stack          |
|      |                          | (``compose.local.yml``): PostgreSQL, Redis, and MinIO.       |
+------+--------------------------+--------------------------------------------------------------+
| 6    | *(10s pause)*            | Waits for infrastructure containers to become healthy        |
|      |                          | before proceeding.                                           |
+------+--------------------------+--------------------------------------------------------------+
| 7    | ``just db-migrate``      | Applies all pending Alembic migrations to bring the          |
|      |                          | database schema to the current version.                      |
+------+--------------------------+--------------------------------------------------------------+
| 8    | ``just server``          | Launches the FastAPI/Uvicorn API server in a new terminal    |
|      |                          | window.                                                      |
+------+--------------------------+--------------------------------------------------------------+
| 9    | ``just worker-default``  | Launches the default Celery worker (post-processing tasks)   |
|      |                          | in a new terminal window.                                    |
+------+--------------------------+--------------------------------------------------------------+
| 10   | ``just worker-inference``| Launches the inference Celery worker (GPU-accelerated pose   |
|      |                          | estimation tasks) in a new terminal window.                  |
+------+--------------------------+--------------------------------------------------------------+
| 11   | *(health polling)*       | Polls ``GET /health/shallow/`` until the server responds     |
|      |                          | with HTTP 200 or the retry limit is reached.                 |
+------+--------------------------+--------------------------------------------------------------+
| 12   | *(Swagger UI opening)*   | On successful health check, automatically opens the Swagger  |
|      |                          | UI in the default browser. If the server fails to respond    |
|      |                          | in time, prints a warning with the manual URL.               |
+------+--------------------------+--------------------------------------------------------------+

Usage
-----
pixi run python scripts/quick_start/local.py

Note:
-----
The exact shell commands executed by each ``just`` recipe are defined in the
project's ``justfile`` at the repository root. Each recipe is documented with
inline comments describing its purpose, arguments, and the underlying processes
it spawns. Refer to the ``justfile`` for the authoritative, step-by-step
implementation details of the bootstrap sequence.
"""
from .shared import (
    terminal, 
    get_api_urls, 
    start_infrastructure, 
    check_health_and_open_docs
)

if __name__ == "__main__":

    start_infrastructure()

    terminal(["just", "server"])
    terminal(["just", "worker-default"])
    terminal(["just", "worker-inference"])

    urls = get_api_urls()

    check_health_and_open_docs(urls)