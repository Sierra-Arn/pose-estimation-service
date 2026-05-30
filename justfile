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

# =============================================================================
# Justfile Settings
# =============================================================================
set dotenv-load := true
set export := true

# =============================================================================
# Environment Mappings: justfile variable -> pixi environment
# =============================================================================

ENV_DEFAULT     := "pixi run -e default"        
ENV_SERVER      := "pixi run -e server"         
ENV_WORKER_INF  := "pixi run -e worker-inference"
ENV_WORKER_DEF  := "pixi run -e worker-default"

# =============================================================================
# Scripts
# =============================================================================

# Generate .env from template with secure random passwords
gen-env template='local':
    {{ENV_DEFAULT}} python scripts/infra/init_env.py --template {{template}}

# Generate Redis ACL rules for Docker init
gen-acl:
    {{ENV_DEFAULT}} python scripts/infra/generate_redis_acl.py

# Generate PostgreSQL user creation script for Docker init
gen-sql:
    {{ENV_DEFAULT}} python scripts/infra/generate_postgres_sql.py

# Generate MinIO policy and init script for Docker init container
gen-minio:
    {{ENV_DEFAULT}} python scripts/infra/generate_minio_setup.py

# Export OpenAPI specification to local file
export-swagger:
    {{ENV_SERVER}} python scripts/utils/export_swagger.py

# =============================================================================
# Infrastructure
# =============================================================================

# Generate new revision
db-revision message='New migration':
    {{ENV_SERVER}} alembic -c ./migrations/alembic.ini revision -m "{{message}}"

# Generate new revision with auto-detected changes
db-revision-auto message='Auto migration':
    {{ENV_SERVER}} alembic -c ./migrations/alembic.ini revision --autogenerate -m "{{message}}"

# Apply pending migrations to sync database schema
db-migrate:
    {{ENV_SERVER}} alembic -c ./migrations/alembic.ini upgrade head

# Revert the latest migration step
db-rollback:
    {{ENV_SERVER}} alembic -c ./migrations/alembic.ini downgrade -1

# =============================================================================
# Runtime
# =============================================================================

# Start Celery worker for ML inference
worker-inference:
    {{ENV_WORKER_INF}} python -m app.workers.inference.main

# Start Celery worker for general-purpose background tasks
worker-default:
    {{ENV_WORKER_DEF}} python -m app.workers.default.main

# Launch FastAPI server
server:
    {{ENV_SERVER}} python -m app.server.main

# =============================================================================
# Docker Local
# =============================================================================

# Start infrastructure stack to be consumed by locally running services
docker-local-up:
    {{ENV_DEFAULT}} docker compose -f docker/compose.local.yml up -d

# Stop local containers and remove anonymous volumes
docker-local-down:
    {{ENV_DEFAULT}} docker compose -f docker/compose.local.yml down --remove-orphans --volumes

# Stream combined logs from all local services
docker-local-logs:
    {{ENV_DEFAULT}} docker compose -f docker/compose.local.yml logs -f

# =============================================================================
# Docker Deploy
# =============================================================================

# Launch fully containerized stack with infrastructure, API server, and workers
docker-deploy-up:
    {{ENV_DEFAULT}} docker compose -f docker/compose.deploy.yml up --build -d

# Stop production containers and clean up unused networks/volumes
docker-deploy-down:
    {{ENV_DEFAULT}} docker compose -f docker/compose.deploy.yml down --remove-orphans --volumes

# Stream combined logs from all production services
docker-deploy-logs:
    {{ENV_DEFAULT}} docker compose -f docker/compose.deploy.yml logs -f

# =============================================================================
# Quick Start
# =============================================================================

# Start full local development environment and open Swagger in browser
quick-start-local:
    {{ENV_DEFAULT}} python scripts/quick_start/local.py

# Start full containerized deployment and open Swagger in browser
quick-start-deploy:
    {{ENV_DEFAULT}} python scripts/quick_start/deploy.py