# app/running_analysis/body_angles.py
import numpy as np
from .types import AnatomicalSide
from ..human_pose_estimator.types import KeypointMap2D


def _calculate_angle_between_vectors(
    vec1: np.ndarray,
    vec2: np.ndarray
) -> float:
    """
    Compute the angle between two 2D vectors in degrees.

    Parameters
    ----------
    vec1 : np.ndarray
        First input vector of shape `(2,)`.
    vec2 : np.ndarray
        Second input vector of shape `(2,)`.

    Returns
    -------
    float
        Angle in degrees in the range `[0.0, 180.0]`.
    """

    dot = np.dot(vec1, vec2)
    norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)

    # Guard against near-zero product of vector magnitudes to avoid division by zero
    if norm < 1e-8:
        return 0.0

    cosine = np.clip(dot / norm, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def _get_keypoint_coords(
    keypoints: KeypointMap2D,
    name: str
) -> np.ndarray | None:
    """
    Safely extract (x, y) coordinates of a named keypoint as a NumPy array.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary-like mapping of keypoint names to keypoint objects.
    name : str
        Name of the keypoint (e.g., "right_shoulder").

    Returns
    -------
    np.ndarray or None
        Shape `(2,)` array `[x, y]` if keypoint exists, else `None`.
    """

    if name not in keypoints:
        return None
    kp = keypoints[name]
    return np.array([kp.x, kp.y], dtype=np.float64)


def _apply_side_based_sign(
    angle: float,
    side: AnatomicalSide,
    displacement_x: float
) -> float:
    """
    Apply sign to an unsigned angle based on anatomical side and horizontal displacement.

    In side-view biomechanics, "forward" direction depends on which side is visible:
      - RIGHT profile: subject moves right -> forward = +X -> displacement_x > 0
      - LEFT  profile: subject moves left  -> forward = -X -> displacement_x < 0

    A positive returned angle always indicates forward orientation/motion.

    Parameters
    ----------
    angle : float
        Unsigned angle in degrees (expected in [0, 180]).
    side : AnatomicalSide
        Anatomical side corresponding to the camera view.
    displacement_x : float
        Horizontal component (X) of the biomechanical vector of interest
        (e.g., torso = shoulder.x - hip.x).

    Returns
    -------
    float
        Signed angle where `>0` means forward relative to motion direction.
    """

    if side == AnatomicalSide.RIGHT:
        is_forward = displacement_x > 0
    else:  # AnatomicalSide.LEFT
        is_forward = displacement_x < 0

    return angle if is_forward else -angle


def calculate_knee_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute knee angle (hip-knee-ankle).

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Knee angle in degrees, or `None` if required keypoints are missing.
    """

    hip = _get_keypoint_coords(keypoints, f"{side}_hip")
    knee = _get_keypoint_coords(keypoints, f"{side}_knee")
    ankle = _get_keypoint_coords(keypoints, f"{side}_ankle")

    if hip is None or knee is None or ankle is None:
        return None

    thigh = hip - knee
    shank = ankle - knee
    return _calculate_angle_between_vectors(thigh, shank)


def calculate_hip_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute hip angle (shoulder-hip-knee).

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Hip angle in degrees, or `None` if required keypoints are missing.
    """

    shoulder = _get_keypoint_coords(keypoints, f"{side}_shoulder")
    hip = _get_keypoint_coords(keypoints, f"{side}_hip")
    knee = _get_keypoint_coords(keypoints, f"{side}_knee")

    if shoulder is None or hip is None or knee is None:
        return None

    torso = shoulder - hip
    thigh = knee - hip
    return _calculate_angle_between_vectors(torso, thigh)


def calculate_trunk_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute trunk lean angle relative to vertical.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Side used to define torso vector. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Signed trunk angle in degrees (`>0` = forward lean), or `None` if missing keypoints.
    """

    shoulder = _get_keypoint_coords(keypoints, f"{side}_shoulder")
    hip = _get_keypoint_coords(keypoints, f"{side}_hip")

    if shoulder is None or hip is None:
        return None

    torso = shoulder - hip
    vertical = np.array([0.0, -1.0])
    angle = _calculate_angle_between_vectors(torso, vertical)
    return _apply_side_based_sign(angle, side, torso[0])


def calculate_arm_swing_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute arm swing angle relative to torso.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Signed arm swing angle in degrees (`>0` = forward swing), or `None` if missing keypoints.
    """

    shoulder = _get_keypoint_coords(keypoints, f"{side}_shoulder")
    elbow = _get_keypoint_coords(keypoints, f"{side}_elbow")
    hip = _get_keypoint_coords(keypoints, f"{side}_hip")

    if shoulder is None or elbow is None or hip is None:
        return None

    torso = shoulder - hip
    upper_arm = elbow - shoulder
    angle = _calculate_angle_between_vectors(torso, upper_arm)
    return _apply_side_based_sign(angle, side, upper_arm[0])


def calculate_elbow_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute elbow flexion angle (shoulder-elbow-wrist).

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Elbow angle in degrees, or `None` if required keypoints are missing.
    """

    shoulder = _get_keypoint_coords(keypoints, f"{side}_shoulder")
    elbow = _get_keypoint_coords(keypoints, f"{side}_elbow")
    wrist = _get_keypoint_coords(keypoints, f"{side}_wrist")

    if shoulder is None or elbow is None or wrist is None:
        return None

    upper_arm = shoulder - elbow
    forearm = wrist - elbow
    return _calculate_angle_between_vectors(upper_arm, forearm)


def calculate_shank_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute shank (lower leg) angle relative to vertical.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Signed shank angle in degrees (`>0` = forward tilt), or `None` if required keypoints are missing.
    """

    knee = _get_keypoint_coords(keypoints, f"{side}_knee")
    ankle = _get_keypoint_coords(keypoints, f"{side}_ankle")

    if knee is None or ankle is None:
        return None

    shank = ankle - knee
    vertical = np.array([0.0, 1.0])  # downward
    angle = _calculate_angle_between_vectors(shank, vertical)
    return _apply_side_based_sign(angle, side, shank[0])


def calculate_hip_ankle_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute hip-to-ankle alignment angle relative to vertical.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Hip-ankle angle in degrees, or `None` if required keypoints are missing.

    Notes
    -----
    This angle reflects overall leg posture (e.g., overstriding if too extended).
    The vector runs from hip to ankle; reference is downward vertical `[0, 1]`.
    """

    hip = _get_keypoint_coords(keypoints, f"{side}_hip")
    ankle = _get_keypoint_coords(keypoints, f"{side}_ankle")

    if hip is None or ankle is None:
        return None

    leg = ankle - hip
    vertical = np.array([0.0, 1.0])
    return _calculate_angle_between_vectors(leg, vertical)


def calculate_head_angle(
    keypoints: KeypointMap2D,
    side: AnatomicalSide = AnatomicalSide.RIGHT
) -> float | None:
    """
    Compute head alignment angle relative to torso.

    Parameters
    ----------
    keypoints : KeypointMap2D
        Dictionary of detected 2D keypoints.
    side : AnatomicalSide, optional
        Anatomical side to evaluate. Default is `AnatomicalSide.RIGHT`.

    Returns
    -------
    float or None
        Head-torso angle in degrees, or `None` if required keypoints are missing.

    Notes
    -----
    The head vector is defined from ear to eye (approximating neck orientation).
    The torso vector is defined from shoulder to hip.
    A smaller angle indicates better alignment; large deviations may suggest
    excessive neck extension or flexion.
    """

    ear = _get_keypoint_coords(keypoints, f"{side}_ear")
    eye = _get_keypoint_coords(keypoints, f"{side}_eye")
    shoulder = _get_keypoint_coords(keypoints, f"{side}_shoulder")
    hip = _get_keypoint_coords(keypoints, f"{side}_hip")

    if ear is None or eye is None or shoulder is None or hip is None:
        return None

    head_vector = eye - ear
    torso_vector = hip - shoulder
    return _calculate_angle_between_vectors(head_vector, torso_vector)