# app/running_analysis/__init__.py
from statistics import fmean
from .types import AnatomicalSide, SingleFrameAnalysis, VideoAnalysis
from .body_angles import (
    calculate_knee_angle,
    calculate_hip_angle,
    calculate_trunk_angle,
    calculate_arm_swing_angle,
    calculate_elbow_angle,
    calculate_shank_angle,
    calculate_hip_ankle_angle,
    calculate_head_angle
)
from ..human_pose_estimator.types import KeypointMap2D


def analyze_single_frame(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> SingleFrameAnalysis:
    """
    Compute all available running angles for a single frame.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Detected 2D keypoints for one frame.
    side : AnatomicalSide, optional
        Anatomical side to use for signed angles. Default is RIGHT.

    Returns
    -------
    SingleFrameAnalysis
        Named container with all computed angles (or None if missing).
    """
    return SingleFrameAnalysis(
        knee_angle=calculate_knee_angle(keypoints, side),
        hip_angle=calculate_hip_angle(keypoints, side),
        trunk_angle=calculate_trunk_angle(keypoints, side),
        arm_swing_angle=calculate_arm_swing_angle(keypoints, side),
        elbow_angle=calculate_elbow_angle(keypoints, side),
        shank_angle=calculate_shank_angle(keypoints, side),
        hip_ankle_angle=calculate_hip_ankle_angle(keypoints, side),
        head_angle=calculate_head_angle(keypoints, side),
    )


def analyze_full_video(
    keypoints_sequence: list[KeypointMap2D],
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> VideoAnalysis:
    """
    Compute aggregated running metrics over consecutive frames.

    Parameters
    ----------
    keypoints_sequence : list[KeypointMap2D]
        List of keypoint maps, one per frame.
    side : AnatomicalSide, optional
        Anatomical side to use for signed angles. Default is RIGHT.

    Returns
    -------
    VideoAnalysis
        Aggregated metrics across all valid frames.
        If a metric is missing in all frames, its value is None.
    """
    # Accumulators for mean values
    mean_accum = {
        'knee_angle': [],
        'hip_angle': [],
        'trunk_angle': [],
        'elbow_angle': [],
        'shank_angle': [],
        'hip_ankle_angle': [],
        'head_angle': [],
    }
    arm_swing_values = []  # separate list for min/max

    for keypoints in keypoints_sequence:
        frame = analyze_single_frame(keypoints, side)
        
        # Collect values for mean
        for field in mean_accum:
            value = getattr(frame, field)
            if value is not None:
                mean_accum[field].append(value)
        
        # Collect arm swing separately
        if frame.arm_swing_angle is not None:
            arm_swing_values.append(frame.arm_swing_angle)

    # Compute means
    means = {}
    for field, values in mean_accum.items():
        means[f"mean_{field}"] = fmean(values) if values else None

    # Compute arm swing range
    arm_min = min(arm_swing_values) if arm_swing_values else None
    arm_max = max(arm_swing_values) if arm_swing_values else None

    return VideoAnalysis(
        min_arm_swing_angle=arm_min,
        max_arm_swing_angle=arm_max,
        **means
    )