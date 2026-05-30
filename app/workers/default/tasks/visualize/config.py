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

# app/shared/visualizer/config.py
from dataclasses import dataclass
import cv2


@dataclass(frozen=True)
class VisualizerConfig:
    """
    Immutable configuration for frame overlay rendering parameters.

    Contains fixed visual styling constants used throughout the pose
    estimation visualization pipeline. Values are resolved at module
    import time and cannot be mutated to ensure deterministic rendering
    behavior across all Celery worker instances.

    Attributes
    ----------
    bbox_color : tuple of int
        OpenCV BGR color for detection bounding boxes.
    keypoint_color : tuple of int
        OpenCV BGR color for individual keypoint markers.
    text_color : tuple of int
        OpenCV BGR color for confidence score labels.
    overlay_alpha : float
        Transparency factor for alpha blending overlays onto base frames.
        Value ranges from 0.0 fully transparent to 1.0 fully opaque.
    line_thickness : int
        Stroke width in pixels for bounding boxes and skeleton connections.
    keypoint_radius : int
        Radius in pixels for filled keypoint circles.
    font : int
        OpenCV font face identifier for text rendering.
    font_scale : float
        Scaling factor for font size relative to the base font metrics.
    font_thickness : int
        Stroke width in pixels for rendered text characters.
    """

    bbox_color: tuple[int, int, int] = (0, 255, 0)
    keypoint_color: tuple[int, int, int] = (0, 0, 255)
    text_color: tuple[int, int, int] = (255, 255, 255)
    overlay_alpha: float = 0.6
    line_thickness: int = 2
    keypoint_radius: int = 3
    font: int = cv2.FONT_HERSHEY_SIMPLEX
    font_scale: float = 0.5
    font_thickness: int = 1

visualizer_config = VisualizerConfig()