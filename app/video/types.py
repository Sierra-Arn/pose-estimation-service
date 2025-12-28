# app/video/types.py
import cv2


class VisualizerStyle:
    """
    A container for immutable visual styling constants used in pose and detection visualization.

    These values define the appearance of bounding boxes, keypoints, skeleton edges, and text.
    They are intentionally **not configurable via environment variables** because
    skeleton rendering involves a large number of per-joint color and connectivity parameters,
    which are already hardcoded for maintainability.
    
    Allowing partial customization (e.g., keypoint radius via `.env` while joint colors remain fixed)
    would create an inconsistent and confusing configuration surface. Therefore, all visual
    parameters — including colors, radii, line thickness, opacity, fonts, and video properties —
    are defined as immutable constants in this class.

    Attributes
    ----------
    BBOX_COLOR : tuple[int, int, int]
        RGB color for the person bounding box (YOLO detection).
        Format: `(R, G, B)` with values in `[0, 255]`.
        Default: `(0, 255, 0)` (green).

    KEYPOINT_COLOR : tuple[int, int, int]
        RGB color for keypoint circles.
        Default: `(0, 0, 255)` (red).

    KEYPOINT_RADIUS : int
        Radius (in pixels) of drawn keypoint circles.
        Default: `4`.

    KEYPOINT_FILLED : int
        Thickness for filled circles (`-1` means filled).
        Default: `-1`.

    KEYPOINT_ALPHA : float
        Opacity for keypoint overlays (`0.0` = transparent, `1.0` = opaque).
        Default: `0.8`.

    LINE_THICKNESS : int
        Thickness (in pixels) for skeleton lines and bounding boxes.
        Default: `2`.

    CONFIDENCE_FONT : int
        OpenCV font type for confidence score text.
        Default: `cv2.FONT_HERSHEY_SIMPLEX`.

    CONFIDENCE_FONT_SCALE : float
        Font scale for confidence score text.
        Default: `0.4`.

    CONFIDENCE_FONT_COLOR : tuple[int, int, int]
        RGB color for confidence score text.
        Default: `(255, 255, 255)` (white).

    CONFIDENCE_FONT_THICKNESS : int
        Thickness of confidence score text.
        Default: `1`.

    VIDEO_FPS : float
        Frames per second for output video.
        Default: `30.0`.

    BLEND_WEIGHT : int
        Weight for `cv2.addWeighted` when blending overlay with original frame.
        Should always be `0` (no additional scaling).
        Default: `0`.
    """

    # Bounding box
    BBOX_COLOR: tuple[int, int, int] = (0, 255, 0)

    # Keypoints
    KEYPOINT_COLOR: tuple[int, int, int] = (0, 0, 255)
    KEYPOINT_RADIUS: int = 4
    KEYPOINT_FILLED: int = -1  # OpenCV constant for filled circle
    KEYPOINT_ALPHA: float = 0.8

    # Skeleton & lines
    LINE_THICKNESS: int = 2

    # Confidence text (for debugging)
    CONFIDENCE_FONT: int = cv2.FONT_HERSHEY_SIMPLEX
    CONFIDENCE_FONT_SCALE: float = 0.4
    CONFIDENCE_FONT_COLOR: tuple[int, int, int] = (255, 255, 255)
    CONFIDENCE_FONT_THICKNESS: int = 1

    # Video
    VIDEO_FPS: float = 30.0

    # Blending
    BLEND_WEIGHT: int = 0  # third weight in cv2.addWeighted