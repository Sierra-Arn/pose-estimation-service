# app/running_analysis/types.py
from enum import StrEnum
from typing import NamedTuple


class AnatomicalSide(StrEnum):
    """
    Anatomical side to analyze in a side-view running assessment.

    Used to avoid code duplication: biomechanical angles (knee, hip, etc.)
    are computed identically for left and right limbs — only keypoint names differ.
    This enum enables a single generic implementation per metric.
    
    Notes
    -----
    This enum inherits from `enum.StrEnum`, meaning each member is a native `str` instance. 
    Therefore, it can be used directly in any context expecting a string 
    without needing to access the `.value` attribute.
    """

    LEFT = "left"
    RIGHT = "right"


class SingleFrameAnalysis(NamedTuple):
    """
    Container for aggregated running metrics over a frame.

    A value of `None` indicates the metric could not be computed
    (e.g., due to missing keypoints).
    """

    knee_angle: float | None = None
    hip_angle: float | None = None
    trunk_angle: float | None = None
    arm_swing_angle: float | None = None
    elbow_angle: float | None = None
    shank_angle: float | None = None
    hip_ankle_angle: float | None = None
    head_angle: float | None = None


class VideoAnalysis(NamedTuple):
    """
    Container for aggregated running metrics over consecutive frames.

    A value of `None` indicates the metric could not be computed
    (e.g., due to missing keypoints).
    """

    mean_knee_angle: float | None = None
    mean_hip_angle: float | None = None
    mean_trunk_angle: float | None = None
    max_arm_swing_angle: float | None = None
    min_arm_swing_angle: float | None = None
    mean_elbow_angle: float | None = None
    mean_shank_angle: float | None = None
    mean_hip_ankle_angle: float | None = None
    mean_head_angle: float | None = None