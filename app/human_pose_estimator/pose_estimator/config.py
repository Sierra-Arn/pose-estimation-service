# app/human_pose_estimator/pose_estimator/config.py
import os
from typing import ClassVar
from pydantic import Field, field_validator
import torch
from ..types import DeviceType, KeypointFormat
from ...shared import BaseConfig


class PoseEstimatorConfig(BaseConfig):
    """
    Configuration schema for the Sapiens-based human pose estimation module.

    Attributes
    ----------
    model_path : str
        Path to the TorchScript pose estimation model file. The model file must exist.
    device : DeviceType
        Device to run inference on. Default is `DeviceType.CUDA`.
    keypoint_format : KeypointFormat
        Semantic format of the model's output keypoints. 
        This field must match the architecture of the loaded model.
        Default is `KeypointFormat.COCO`.
    keypoint_confidence_threshold : float
        Confidence threshold for detection filtering. Detections with confidence
        below this value are discarded. Must be in range `[0.0, 1.0]`. Default is `0.3`.

    Notes
    -----
    This class inherits from `app.shared.base_config.BaseConfig`.
    For details on configuration loading behavior, see its documentation.
    """

    env_prefix: ClassVar[str] = "POSE_ESTIMATOR_"

    model_path: str
    device: DeviceType = Field(default=DeviceType.CUDA)
    keypoint_format: KeypointFormat = Field(default=KeypointFormat.COCO)
    keypoint_confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        abs_path = os.path.abspath(v)
        if not os.path.isfile(abs_path):
            raise ValueError(f"Pose estimation model file not found at path: '{abs_path}'.")
        return abs_path

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: DeviceType) -> DeviceType:
        if v == DeviceType.CUDA and not torch.cuda.is_available():
            raise ValueError(
                "CUDA device requested, but `torch.cuda.is_available()` returned False."
            )
        return v


# Unlike application-level settings (e.g., REST API or MinIO configuration),
# which are global to a single service instance,
# multiple independent model wrapper instances may coexist within the same process (e.g., one per worker thread).
# Therefore, neither the configuration nor the model should be implemented as a singleton.