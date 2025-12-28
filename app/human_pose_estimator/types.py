# app/human_pose_estimator/types.py
from typing import NamedTuple
from enum import StrEnum
import numpy as np
from numpy.typing import NDArray


RGBFrame = NDArray[np.uint8]
"""
A single video frame in RGB color format.

This type represents a standard image as a NumPy array with the following properties:
- **Shape**: `(H, W, 3)`, where `H` is height, `W` is width, and `3` corresponds to Red, Green, Blue channels.
- **Data type**: `uint8` (values in `[0, 255]`).
- **Channel order**: RGB (Red at index 0, Green at 1, Blue at 2).
"""


class BBox(NamedTuple):
    """
    Bounding box in `(x1, y1, x2, y2)` format.

    Coordinates are in pixel space, where:
    - `(x1, y1)` is the top-left corner,
    - `(x2, y2)` is the bottom-right corner.
    """
    x1: int
    y1: int
    x2: int
    y2: int


class Keypoint2D(NamedTuple):
    """
    A single human keypoint with 2D spatial coordinates and confidence.

    Attributes
    ----------
    x : float
        Horizontal coordinate in original image pixel space.
    y : float
        Vertical coordinate in original image pixel space.
    confidence : float
        Detection confidence score in [0.0, 1.0].
    """

    x: float
    y: float
    confidence: float


KeypointMap2D = dict[str, Keypoint2D]
"""
Mapping from semantic keypoint names (e.g., `'nose'`, `'left_elbow'`) to keypoint instances. 
The set of keys depends on the pose model's output format (e.g., COCO, COCO-WholeBody, Goliath).
"""


class PoseEstimationResult2D(NamedTuple):
    """
    Result of human pose estimation on a single frame.

    Attributes
    ----------
    bbox : BBox | None
        Bounding box of the detected person in original image coordinates
        as `(x1, y1, x2, y2)`. 
        May be `None` if no person was detected.

    keypoints : KeypointMap2D
        Dictionary mapping keypoint names (e.g., `'nose'`, `'left_elbow'`)
        to keypoint objects in **original image coordinates**.
        May be `{}` if pose estimation fails or no keypoints are visible. 

    Note
    ----
    The choice to use `None` for `bbox` and an empty dict `{}` for `keypoints` is intentional
    and reflects common practices in computer vision and software design.

    Bounding boxes are often nullable in detection APIs — many models return `None`,
    empty arrays, or similar sentinel values when no object is found — so `None` fits naturally
    with existing CV pipelines.

    In contrast, representing missing keypoints as an empty dictionary simplifies downstream code:
    it allows safe iteration, key lookup (e.g., with `.get()`), and dictionary operations
    without requiring explicit `is not None` checks. This leads to cleaner, more robust code.
    """

    bbox: BBox | None
    keypoints: KeypointMap2D


class DeviceType(StrEnum):
    """
    Computation device target for model inference and tensor operations.

    Specifies the hardware backend on which tensors and models are executed.
    The selected device has direct implications for performance, memory usage,
    and system requirements.

    - ``"cpu"``: Executes computations on the central processing unit. 
        Universally available, requires no specialized hardware or drivers, 
        but significantly slower for large-scale deep learning workloads.
    - ``"cuda"``: Executes computations on an NVIDIA GPU using the CUDA runtime. 
        Offers orders-of-magnitude speedup for neural network inference and training, 
        but requires a CUDA-capable GPU and properly installed drivers and libraries.

    Notes
    -----
    This enum inherits from `enum.StrEnum`, meaning each member is a native `str` instance. 
    Therefore, it can be used directly in any context expecting a string 
    without needing to access the `.value` attribute.
    """

    CPU = "cpu"
    CUDA = "cuda"


class KeypointFormat(StrEnum):
    """
    Standardized pose estimation formats that define the set of keypoints and skeleton topology.

    Each format corresponds to a specific annotation scheme used in pose estimation 
    datasets or pipelines. The format determines:
    
    - The semantic meaning and count of detected keypoints,
    - The set of valid keypoint names (e.g., `'left_wrist'`, `'nose'`),
    - The skeleton connectivity (edges used for drawing pose skeletons).

    Supported formats:

    - `"coco"`: The 17-keypoint body pose format from the COCO dataset. 
    - `"coco_wholebody"`: An extended variant of COCO with 133 keypoints.
    - `"goliath"`: The body keypoint format used in Meta's **Sapiens** pose estimation models.

    Notes
    -----
    This enum inherits from `enum.StrEnum`, meaning each member is a native `str` instance. 
    Therefore, it can be used directly in any context expecting a string 
    without needing to access the `.value` attribute.
    """

    COCO = "coco"
    COCO_WHOLEBODY = "coco_wholebody"
    GOLIATH = "goliath"