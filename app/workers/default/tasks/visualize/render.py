# Copyright (c) 2026 Ilya Snegov (aka Sierra Arn)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# app/workers/default/tasks/visualize/render.py
import cv2
import numpy as np
from ensam3d_inference import FramePoseResult
from ensam3d_inference.preprocessor.detector.types import RGBFrame
from ensam3d_inference.examples.keypoints import SKELETON, KEYPOINTS
from .config import visualizer_config


def _draw_bbox(image: RGBFrame, bbox: np.ndarray) -> None:
    """
    Render a detection bounding box on the target image.

    Parameters
    ----------
    image : RGBFrame
        Image array modified in-place.
    bbox : np.ndarray
        Coordinates [x1, y1, x2, y2]. Must be a valid 1D array.
    """
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        visualizer_config.bbox_color,
        visualizer_config.line_thickness,
    )


def _draw_bbox_confidence(image: RGBFrame, bbox: np.ndarray, confidence: float) -> None:
    """
    Render detection confidence score as text near the bounding box.

    Parameters
    ----------
    image : RGBFrame
        Image array modified in-place.
    bbox : np.ndarray
        Coordinates [x1, y1, x2, y2]. Used for text positioning.
    confidence : float
        Scalar detection score formatted to two decimal places.
    """
    x1, y1 = map(int, bbox[:2])
    label = f"{confidence:.2f}"
    cv2.putText(
        image,
        label,
        (x1, max(y1 - 8, 10)),
        visualizer_config.font,
        visualizer_config.font_scale,
        visualizer_config.text_color,
        visualizer_config.font_thickness,
    )


def _draw_keypoints(image: RGBFrame, keypoints: np.ndarray, width: int, height: int) -> None:
    """
    Render individual keypoint markers as filled circles using per-keypoint
    semantic colors defined in KEYPOINTS.

    Parameters
    ----------
    image : RGBFrame
        Image array modified in-place.
    keypoints : np.ndarray
        Array of shape (N, 2) containing (x, y) pixel coordinates.
        Extra dimensions are flattened automatically.
    width : int
        Frame width for coordinate clipping.
    height : int
        Frame height for coordinate clipping.

    Raises
    ------
    IndexError
        If keypoints contains more entries than defined in KEYPOINTS.
        This signals a desynchronization between the model output
        topology and the upstream keypoint definition.
    """
    if keypoints.ndim != 2 or keypoints.shape[1] != 2:
        keypoints = keypoints.reshape(-1, 2)

    kp_x = np.clip(keypoints[:, 0], 0, width - 1).astype(int)
    kp_y = np.clip(keypoints[:, 1], 0, height - 1).astype(int)
    valid_mask = (keypoints[:, 0] >= 0) & (keypoints[:, 1] >= 0)

    for i in range(len(keypoints)):
        if valid_mask[i]:
            cv2.circle(
                image,
                (kp_x[i], kp_y[i]),
                visualizer_config.keypoint_radius,
                KEYPOINTS[i].color,
                -1,
            )


def _draw_skeleton(image: RGBFrame, keypoints: np.ndarray, width: int, height: int) -> None:
    """
    Render skeletal connections between keypoints using the SKELETON topology.

    Parameters
    ----------
    image : RGBFrame
        Image array modified in-place.
    keypoints : np.ndarray
        Array of shape (N, 2) containing (x, y) pixel coordinates.
        Extra dimensions are flattened automatically.
    width : int
        Frame width for coordinate clipping.
    height : int
        Frame height for coordinate clipping.
    """
    if keypoints.ndim != 2 or keypoints.shape[1] != 2:
        keypoints = keypoints.reshape(-1, 2)

    kp_x = np.clip(keypoints[:, 0], 0, width - 1).astype(int)
    kp_y = np.clip(keypoints[:, 1], 0, height - 1).astype(int)
    valid_mask = (keypoints[:, 0] >= 0) & (keypoints[:, 1] >= 0)

    for link in SKELETON:
        if valid_mask[link.start] and valid_mask[link.end]:
            cv2.line(
                image,
                (kp_x[link.start], kp_y[link.start]),
                (kp_x[link.end], kp_y[link.end]),
                link.color,
                visualizer_config.line_thickness,
            )


def render_frame(
    frame: RGBFrame,
    result: FramePoseResult | None,
    output: RGBFrame,
    show_bbox: bool = False,
    show_bbox_confidence: bool = False,
    show_keypoints: bool = False,
    show_skeleton: bool = False,
) -> RGBFrame:
    """
    Draw pose estimation overlays onto a single video frame.

    Copies the input frame to the output buffer and draws annotations
    directly on top of it. This preserves the original background
    brightness and avoids global alpha blending artifacts.

    Parameters
    ----------
    frame : RGBFrame
        Input frame in BGR format, typically uint8 with shape (H, W, 3).
    result : FramePoseResult or None
        Inference output for the current frame.
    output : np.ndarray
        Pre-allocated buffer for the final result. Must match frame
        shape and dtype. Written in-place and returned.
    show_bbox : bool, optional
        Render detection bounding box. Default is False.
    show_bbox_confidence : bool, optional
        Render detection confidence text. Evaluated only if show_bbox is True.
        Default is False.
    show_keypoints : bool, optional
        Render keypoint markers. Default is False.
    show_skeleton : bool, optional
        Render skeletal connections. Evaluated only if show_keypoints is True.
        Default is False.

    Returns
    -------
    RGBFrame
        Annotated frame. Points to the same memory as output.
    """
    if result is None or not any((
        show_bbox,
        show_bbox_confidence,
        show_keypoints,
        show_skeleton,
    )):
        return frame.copy()

    output[:] = frame
    height, width = frame.shape[:2]

    if show_bbox:
        bbox_np = result.detection.coords.detach().cpu().numpy()
        _draw_bbox(output, bbox_np)

        if show_bbox_confidence:
            conf_val = float(result.detection.confidence.detach().cpu().numpy())
            _draw_bbox_confidence(output, bbox_np, conf_val)

    if show_keypoints:
        kp_np = result.pose.pred_keypoints_2d.detach().cpu().numpy()
        _draw_keypoints(output, kp_np, width, height)

        if show_skeleton:
            _draw_skeleton(output, kp_np, width, height)

    return output