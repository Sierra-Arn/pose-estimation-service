# app/pickle_data/output.py
import pickle
from typing import Any, Sequence
from io import BytesIO
from ..s3 import files_service
from ..human_pose_estimator import PoseEstimationResult2D
from ..running_analysis.types import VideoAnalysis


def _save_pickle_to_minio(obj: Any, storage_key: str) -> None:
    """Low-level helper to save any object to MinIO as pickle."""
    buffer = BytesIO()
    pickle.dump(obj, buffer)
    buffer.seek(0)
    files_service.upload_fileobj(storage_key, buffer)


def save_estimation_results_to_minio(
    estimation_results: Sequence[PoseEstimationResult2D],
    storage_key: str
) -> None:
    """
    Save pose estimation results to MinIO as a pickle file.

    Parameters
    ----------
    estimation_results : Sequence[PoseEstimationResult2D]
        Pose results for consecutive frames.
    storage_key : str
        MinIO object key.
    """
    _save_pickle_to_minio(estimation_results, storage_key)


def save_running_analysis_to_minio(
    analysis: VideoAnalysis,
    storage_key: str
) -> None:
    """
    Save running analysis to MinIO as a pickle file.

    Parameters
    ----------
    analysis : VideoAnalysis
        Aggregated running metrics over consecutive frames.
    storage_key : str
        MinIO object key.
    """
    _save_pickle_to_minio(analysis, storage_key)