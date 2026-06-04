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

# packages/scripts/src/scripts/quick_start/deploy.py
"""
Production deployment quick-start script.

This script automates the bootstrap process for running the application in a
production or staging environment. It sequentially generates configuration
files and spins up the fully containerized Docker stack, including all
services and workers.

Upon successful startup, the script polls the server's health endpoint and
automatically opens the Swagger UI in the default browser.

Execution sequence:

+------+-------------------------+-------------------------------------------------------------+
| Step | Command / Action        | Description                                                 |
+======+=========================+=============================================================+
| 1    | ``just gen-env deploy`` | Copies ``config/.env.deploy.example`` to ``.env`` in the    |
|      |                         | project root and generates cryptographically secure random  |
|      |                         | passwords for all credential fields. Skipped if ``.env``    |
|      |                         | already exists.                                             |
+------+-------------------------+-------------------------------------------------------------+
| 2    | ``just gen-acl``        | Generates ``docker/redis/init/01-create-users.acl`` from    |
|      |                         | environment variables. Defines Redis users with scoped      |
|      |                         | permissions for the application.                            |
+------+-------------------------+-------------------------------------------------------------+
| 3    | ``just gen-sql``        | Generates ``docker/postgres/init/01-create-user.sql`` from  |
|      |                         | environment variables. Creates the application database     |
|      |                         | user with the minimum required privileges.                  |
+------+-------------------------+-------------------------------------------------------------+
| 4    | ``just gen-minio``      | Generates ``docker/minio/init/policy.json`` and             |
|      |                         | ``docker/minio/init/setup.sh`` from environment variables.  |
|      |                         | Defines the bucket access policy and the MinIO              |
|      |                         | initialization script that runs inside the init container.  |
+------+-------------------------+-------------------------------------------------------------+
| 5    | ``just docker-deploy-up``| Builds all service images and starts the fully containerized|
|      |                         | Docker Compose stack (``compose.deploy.yml``):              |
|      |                         | infrastructure (PostgreSQL, Redis, MinIO), database         |
|      |                         | migration container, API server, default worker, and        |
|      |                         | inference worker.                                           |
+------+-------------------------+-------------------------------------------------------------+
| 6    | *(health polling)*      | Polls ``GET /health/shallow/`` (using the external port     |
|      |                         | defined in ``.env``) until the API server responds with     |
|      |                         | HTTP 200 or the retry limit (20 attempts, 10s interval) is  |
|      |                         | reached.                                                    |
+------+-------------------------+-------------------------------------------------------------+
| 7    | *(Swagger UI opening)*  | On successful health check, automatically opens the Swagger |
|      |                         | UI in the default browser. If the server fails to respond   |
|      |                         | in time, prints a warning with the manual URL.              |
+------+-------------------------+-------------------------------------------------------------+

Usage
-----
pixi run python scripts/quick_start/deploy.py

Note:
-----
The exact shell commands executed by each ``just`` recipe are defined in the
project's ``justfile`` at the repository root. Each recipe is documented with
inline comments describing its purpose, arguments, and the underlying processes
it spawns. Refer to the ``justfile`` for the authoritative, step-by-step
implementation details of the bootstrap sequence.
"""
from .shared import (
    get_api_urls, 
    start_infrastructure, 
    check_health_and_open_docs
)

if __name__ == "__main__":

    start_infrastructure(deploy=True)
    urls = get_api_urls()
    check_health_and_open_docs(urls)