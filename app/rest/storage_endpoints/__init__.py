# app/rest/storage_endpoints/__init__.py
from .bucket_creation import create_bucket
from .video_upload import upload_video
from .artifacts_deletion import delete_artifacts
from .analysis_download import download_analysis
from .video_download import download_video

from .router import storage_router