# =====================================================
# Justfile Settings
# =====================================================
# Load environment variables from .env file into justfile context
# This allows justfile recipes to reference variables using ${VAR_NAME} syntax
set dotenv-load := true

# Export all loaded environment variables to child processes
# This makes variables available to all commands executed within recipes
# (e.g., docker compose, shell scripts, and other external tools)
set export := true


# =====================================================
# Environment Setup
# =====================================================
# Create a local environment configuration file by copying .env.example to .env
# After copying, edit .env file to set your specific configuration values
copy-env:
	cp .env.example .env
    

# =====================================================
# MinIO Persistent Storage Management
# =====================================================
# Creates the local directory specified by MINIO_DATA_PATH environment variable
# This directory will store uploaded objects, bucket metadata, and MinIO state
minio-pers-init:
	sudo mkdir -p ${MINIO_DATA_PATH}

# Remove MinIO persistent storage directory and all contents    
minio-pers-del:
	sudo rm -rf ${MINIO_DATA_PATH}


# =====================================================
# Docker Compose: MinIO Server Initialization
# =====================================================
# Start Local MinIO server in detached mode with S3-compatible object storage
minio-up:
	docker compose --env-file .env up -d

# Stop and remove MinIO container
# Persistent data in MINIO_DATA_PATH is preserved for future restarts
minio-down:
	docker compose --env-file .env down