# app/pickle_data/input.py
import pickle
from typing import Any, Sequence
from ..human_pose_estimator import PoseEstimationResult2D
from ..running_analysis import VideoAnalysis
from ..s3 import files_service


def _load_pickle_from_minio(storage_key: str) -> Any:
    """Low-level helper to load any pickled object from MinIO."""
    data = files_service.download_as_bytes(storage_key)
    return pickle.loads(data)


def load_estimation_results_from_minio(
    storage_key: str
) -> Sequence[PoseEstimationResult2D]:
    """
    Load pose estimation results from MinIO pickle file.

    Parameters
    ----------
    storage_key : str
        MinIO object key.

    Returns
    -------
    Sequence[PoseEstimationResult2D]
        Pose results for consecutive frames.
    """
    return _load_pickle_from_minio(storage_key)


def load_running_analysis_from_minio(
    storage_key: str
) -> VideoAnalysis:
    """
    Load running analysis from MinIO pickle file.

    Parameters
    ----------
    storage_key : str
        MinIO object key.

    Returns
    -------
    VideoAnalysis
        Aggregated running metrics over consecutive frames.
    """
    return _load_pickle_from_minio(storage_key)