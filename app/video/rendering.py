# app/video/rendering.py
import cv2
import numpy as np
from numpy.typing import NDArray
from .types import VisualizerStyle
from .skeletons import SkeletonEdge, SKELETON_DEFINITIONS
from ..human_pose_estimator.types import BBox, KeypointMap2D, KeypointFormat, RGBFrame


def _draw_bbox(
    overlay: NDArray[np.uint8],
    bbox: BBox,
    color: tuple[int, int, int] = VisualizerStyle.BBOX_COLOR,
    thickness: int = VisualizerStyle.LINE_THICKNESS
) -> None:
    """
    Draw a single bounding box on the provided overlay image in-place.

    The bounding box is rendered as an unfilled rectangle with configurable
    color and line thickness. This function modifies the input `overlay` array.

    Parameters
    ----------
    overlay : NDArray[np.uint8]
        Image array (H, W, 3) in RGB format where the box will be drawn.
        This array is modified in-place.
    bbox : BBox
        Bounding box in format `(x1, y1, x2, y2)` with pixel coordinates.
        Coordinates must be integers and within image bounds.
    color : tuple[int, int, int], optional
        RGB color tuple for the rectangle outline. Defaults to `VisualizerStyle.BBOX_COLOR`.
    thickness : int, optional
        Thickness of the rectangle lines in pixels. Defaults to `VisualizerStyle.LINE_THICKNESS`.

    Notes
    -----
    OpenCV's `cv2.rectangle` expects BGR, but since we operate on an RGB `overlay`
    and later blend it appropriately, the color is interpreted correctly in the final output.
    """
    
    x1, y1, x2, y2 = bbox
    # cv2.rectangle draws in-place; (x1, y1) = top-left, (x2, y2) = bottom-right
    cv2.rectangle(
        overlay, 
        (x1, y1), 
        (x2, y2), 
        color, 
        thickness
    )


def _draw_keypoints(
    overlay: NDArray[np.uint8],
    keypoints: KeypointMap2D,
    draw_confidence: bool = False
) -> None:
    """
    Render pose keypoints and optional confidence scores directly on the overlay.

    Parameters
    ----------
    overlay : NDArray[np.uint8]
        Overlay image (H, W, 3, RGB) on which keypoints and optional confidence
        scores will be rendered. Modified in-place.
    keypoints : KeypointMap2D
        Dictionary mapping keypoint names to `Keypoint2D` objects with x, y, and confidence.
        Must contain at least one keypoint.
    draw_confidence : bool, optional
        If True, render each keypoint's confidence score as floating-point text
        near the keypoint location on the `overlay`. Default is `False`.

    Notes
    -----
    Keypoint coordinates (`x`, `y`) are floats but are rounded to nearest pixel
    for rendering, as OpenCV requires integer pixel positions.
    """

    for kp in keypoints.values():
        # Convert float coordinates to integer pixel positions for OpenCV
        x, y = int(round(kp.x)), int(round(kp.y))
        
        # Draw keypoint as a filled circle on the overlay
        cv2.circle(
            overlay,
            (x, y),
            VisualizerStyle.KEYPOINT_RADIUS,
            VisualizerStyle.KEYPOINT_COLOR,
            VisualizerStyle.KEYPOINT_FILLED
        )
        
        # Draw confidence score on the same overlay (not on a separate base image)
        # This simplifies the pipeline but means text will be semi-transparent after blending.
        if draw_confidence:
            cv2.putText(
                overlay,
                f"{kp.confidence:.2f}",
                (x + 5, y + 5),                 # Offset text slightly to avoid overlap
                VisualizerStyle.CONFIDENCE_FONT,
                VisualizerStyle.CONFIDENCE_FONT_SCALE,
                VisualizerStyle.CONFIDENCE_FONT_COLOR,
                VisualizerStyle.CONFIDENCE_FONT_THICKNESS,
            )


def _draw_skeleton(
    overlay: NDArray[np.uint8],
    keypoints: KeypointMap2D,
    skeleton_edges: list[SkeletonEdge]
) -> None:
    """
    Draw skeletal connections between detected keypoints on the overlay image.

    Parameters
    ----------
    overlay : NDArray[np.uint8]
        Image array (H, W, 3) in RGB format where skeleton lines will be drawn.
        Modified in-place.
    keypoints : KeypointMap2D
        Detected keypoints dictionary. Only keypoint names present in this dict
        are considered for skeleton rendering.
    skeleton_edges : list[SkeletonEdge]
        List of skeleton edge definitions (e.g., from `SKELETON_DEFINITIONS[format]`).
        Each edge must have `.start`, `.end`, and `.color` attributes.

    Notes
    -----
    A line is drawn only if **both** keypoints (`edge.start` and `edge.end`) exist 
    in the input `keypoints` dictionary.
    """

    for edge in skeleton_edges:
        if edge.start in keypoints and edge.end in keypoints:
            start = keypoints[edge.start]
            end = keypoints[edge.end]
            x1, y1 = int(round(start.x)), int(round(start.y))
            x2, y2 = int(round(end.x)), int(round(end.y))
            cv2.line(
                overlay,
                (x1, y1),
                (x2, y2),
                edge.color,
                VisualizerStyle.LINE_THICKNESS
            )


def _blend_pose_overlay(
    overlay: NDArray[np.uint8],
    base_image: NDArray[np.uint8],
    dst: NDArray[np.uint8],
    alpha: float = VisualizerStyle.KEYPOINT_ALPHA,
    gamma: float = VisualizerStyle.BLEND_WEIGHT
) -> None:
    """
    Blend a semi-transparent pose overlay onto a base image, writing result to `dst`.

    This function applies alpha blending to combine a foreground overlay
    (containing keypoints, skeleton, or bounding boxes) with a background
    image, producing a visually smooth composite that preserves both
    the underlying scene and the pose annotations.

    The blending follows the OpenCV formula:
        `dst = alpha * overlay + beta * base_image + gamma`
    where `beta = 1 - alpha`.

    Parameters
    ----------
    overlay : NDArray[np.uint8]
        Foreground image (H, W, 3) in RGB format containing rendered pose elements
        (e.g., circles, lines, rectangles).
    base_image : NDArray[np.uint8]
        Background image (H, W, 3) in RGB format that serves as the base scene.
    dst : NDArray[np.uint8]
        Output array (H, W, 3) where the blended result will be written.
        Must be pre-allocated and have the same shape and dtype as inputs.
    alpha : float, optional
        Weight of the overlay in the blend (range: [0.0, 1.0]).
        Higher values make pose annotations more opaque.
        Defaults to `VisualizerStyle.KEYPOINT_ALPHA`.
    gamma : float, optional
        Scalar added to each sum (typically 0.0 for standard blending).
        Defaults to `VisualizerStyle.BLEND_WEIGHT`.
    """

    cv2.addWeighted(
        src1=overlay,
        alpha=alpha,
        src2=base_image,
        beta=1.0 - alpha,
        gamma=gamma,
        dst=dst
    )


def render_annotated_frame(
    frame: RGBFrame,
    keypoints: KeypointMap2D,
    bounding_box: BBox | None,
    show_bbox: bool = True,
    show_keypoints: bool = True,
    show_confidence: bool = False,
    show_skeleton: bool = True,
    keypoint_format: KeypointFormat = KeypointFormat.COCO
) -> RGBFrame:
    """
    Render pose and detection annotations onto a single RGB frame.

    This function applies visual overlays for bounding boxes, keypoints, confidence scores,
    and skeleton connections based on the provided configuration.

    Parameters
    ----------
    frame : RGBFrame
        Input frame in RGB format with shape `(H, W, 3)` and dtype `uint8`.
    keypoints : KeypointMap2D
        Dictionary mapping keypoint names to `Keypoint2D` instances.
        May be empty.
    bounding_box : BBox or None
        Bounding box as `(x1, y1, x2, y2)` in pixel coordinates, or `None` if no detection.
    show_bbox : bool, optional
        Whether to draw the bounding box. Default is `True`.
    show_keypoints : bool, optional
        Whether to draw keypoints. Default is `True`.
    show_confidence : bool, optional
        Whether to render keypoint confidence scores near each point. Default is `False`.
    show_skeleton : bool, optional
        Whether to draw skeleton connections between keypoints. Default is `True`.
    keypoint_format : KeypointFormat, optional
        Skeleton topology to use for drawing connections.
        Must match the semantic layout of `keypoints`. Default is `KeypointFormat.COCO`.

    Returns
    -------
    RGBFrame
        Annotated frame in RGB format with shape `(H, W, 3)` and dtype `uint8`.
        If no annotations are requested or available, returns a copy of the input frame.
    """

    # Early exit if nothing to annotate
    has_bbox = show_bbox and bounding_box is not None
    has_pose = (show_keypoints or show_skeleton) and bool(keypoints)
    
    if not (has_bbox or has_pose):
        return frame.copy()

    # Resolve skeleton topology
    skeleton_edges = SKELETON_DEFINITIONS[keypoint_format]

    # Start with a copy of the original frame
    overlay = frame.copy()

    # Draw bounding box (opaque, no blending)
    if has_bbox:
        _draw_bbox(overlay=overlay, bbox=bounding_box)

    # Draw pose elements (keypoints and/or skeleton)
    if has_pose:
        if show_keypoints:
            _draw_keypoints(overlay=overlay, keypoints=keypoints, draw_confidence=show_confidence)
        if show_skeleton:
            _draw_skeleton(overlay=overlay, keypoints=keypoints, skeleton_edges=skeleton_edges)

        # Apply semi-transparent blending for pose only (not bbox)
        annotated = np.empty_like(frame)
        _blend_pose_overlay(overlay=overlay, base_image=frame, dst=annotated)
        return annotated

    # Only bbox was drawn — return overlay as-is
    return overlay