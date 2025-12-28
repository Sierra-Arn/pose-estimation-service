# app/human_pose_estimator/human_detector/config.py
import os
from typing import ClassVar
from pydantic import Field, field_validator
from ...shared import BaseConfig


class HumanDetectorConfig(BaseConfig):
    """
    Configuration schema for the human detection module using YOLO.

    Attributes
    ----------
    model_path : str
        Path to the YOLO model weights file. The model file must exist.
    confidence_threshold : float
        Confidence threshold for detection filtering. Detections with confidence
        below this value are discarded. Must be in range `[0.0, 1.0]`. Default is `0.3`.

    Notes
    -----
    This class inherits from `app.shared.base_config.BaseConfig`.
    For details on configuration loading behavior, see its documentation.
    """

    env_prefix: ClassVar[str] = "HUMAN_DETECTOR_"

    model_path: str
    confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        abs_path = os.path.abspath(v)
        if not os.path.isfile(abs_path):
            raise ValueError(f"YOLO model file not found at absolute path: '{abs_path}'.")
        return abs_path

# Unlike application-level settings (e.g., REST API or MinIO configuration),
# which are global to a single service instance,
# multiple independent model wrapper instances may coexist within the same process (e.g., one per worker thread).
# Therefore, neither the configuration nor the model should be implemented as a singleton.