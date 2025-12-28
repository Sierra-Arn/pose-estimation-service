# app/s3/__init__.py
from .config import minio_config
from .client import get_sync_minio_session
from .service import files_service