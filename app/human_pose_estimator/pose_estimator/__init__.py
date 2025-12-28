# app/human_pose_estimator/pose_estimator/__init__.py
import numpy as np
from numpy.typing import NDArray
import torch
from torch.jit import ScriptModule
from .config import PoseEstimatorConfig
from .keypoints import KEYPOINT_FORMATS
from ..utils import create_image_preprocessor
from ..types import RGBFrame, Keypoint2D, KeypointMap2D


class PoseEstimator:
    """
    A Sapiens-based pose estimator that predicts human keypoints in original image coordinates.

    This class wraps the official Sapiens pose estimation model exported in TorchScript format.
    It handles:  
    1. preprocessing, 
    2. inference, 
    3. peak extraction from internal heatmaps,
    4. scaling the results to match the dimensions of the input image.

    Attributes
    ----------
    _model : torch.jit.ScriptModule
        Pre-loaded Sapiens pose estimation model in TorchScript format.
        Loaded from the path specified in the configuration.
    sap_input_size : tuple[int, int]
        The canonical input resolution used internally by the official Sapiens pose estimation model,
        expressed as `(height, width)`. Input images of any size are automatically resized to this
        resolution during preprocessing.
    sap_heatmap_size : tuple[int, int]
        The fixed heatmap resolution of the output of the official Sapiens pose estimation model,
        expressed as `(height, width)`. Keypoint coordinates are automatically scaled from this
        internal representation to match the input image resolution.
    _keypoint_names : list[str]
        Ordered list of keypoint names corresponding to the selected keypoint format
        (e.g., `['nose', 'left_eye', ..., 'right_ankle']` for COCO).
        Determined by the `keypoint_format` setting in the configuration.
    _preprocessor : callable
        Image preprocessing pipeline that converts input images from `(H, W, 3) uint8` NumPy arrays 
        to normalized `(1, 3, H_in, W_in)` float32 tensors suitable for the official Sapiens pose estimator.
    _device : torch.device
        The device (CPU or CUDA) explicitly requested by the user in the configuration, where the model is loaded and inference is performed.
    _confidence_threshold : float
        Minimum confidence score for a keypoint to be included in the output.
        Keypoints with confidence below this value are **excluded** from the returned dictionary.
    """

    @property
    def sap_input_size(self) -> tuple[int, int]:
        """
        The fixed input resolution expected by the official Sapiens pose estimation model.
        
        Returns
        -------
        tuple[int, int]
            Always `(768, 1024)` as (height, width).
        """

        return (768, 1024)

    @property
    def sap_heatmap_size(self) -> tuple[int, int]:
        """
        The fixed spatial dimensions of the output heatmaps produced by the official Sapiens pose estimator.
        
        The model outputs heatmaps that are 4x downsampled relative to the input,
        resulting in a fixed resolution of `(192, 256)` as (height, width).
        
        Returns
        -------
        tuple[int, int]
            Always `(192, 256)` as (height, width).
        """

        return (192, 256)

    def __init__(self, config: PoseEstimatorConfig):
        """
        Initialize the pose estimator using the provided configuration.
        After that validates the model by performing a dummy forward pass.

        Parameters
        ----------
        config : PoseEstimatorConfig
            Configuration object specifying model path, device, keypoint format,
            and keypoint confidence threshold.

        Raises
        ------
        RuntimeError
            If the model fails to load, cannot be executed, or outputs an unexpected
            number of heatmap channels for the configured keypoint format.
        """

        # Store user-provided configuration settings
        self._device = torch.device(config.device)
        self._confidence_threshold = config.keypoint_confidence_threshold

        # Load model and place it directly on the configured device
        self._model: ScriptModule = torch.jit.load(config.model_path)
        self._model.eval()
        self._model.to(self._device)

        # Prepare preprocessing and keypoint metadata
        self._preprocessor = create_image_preprocessor(input_size=self.sap_input_size)
        self._keypoint_names = KEYPOINT_FORMATS[config.keypoint_format]

        # === Validate model integrity using a dummy forward pass ===
        # The dummy input is created on the configured device.
        dummy_input = torch.randn(
            1, 3, self.sap_input_size[0], self.sap_input_size[1],
            dtype=torch.float32,
            device=self._device
        )

        with torch.inference_mode():
            try:
                dummy_output: torch.Tensor = self._model(dummy_input)
            except Exception as e:
                raise RuntimeError(
                    "Failed to execute model with a dummy input. "
                    "Ensure the model is a valid Sapiens pose estimator in TorchScript format."
                ) from e

        # Validate output tensor shape: must be 4D (B, K, Hh, Wh)
        if len(dummy_output.shape) != 4:
            raise RuntimeError(
                f"Model output must be 4D (B, K, Hh, Wh), but got shape {dummy_output.shape}."
            )

        # Validate number of heatmap channels matches expected keypoint count
        num_heatmaps = dummy_output.shape[1]
        expected_keypoints = len(self._keypoint_names)
        if num_heatmaps != expected_keypoints:
            raise RuntimeError(
                f"Model outputs {num_heatmaps} heatmap channels, "
                f"but {expected_keypoints} keypoints are expected "
                f"for keypoint format '{config.keypoint_format}'."
            )

        # Confirm that the model's heatmap resolution matches the official Sapiens specification
        heatmap_height, heatmap_width = dummy_output.shape[2], dummy_output.shape[3]
        if (heatmap_height, heatmap_width) != self.sap_heatmap_size:
            raise RuntimeError(
                f"Model outputs heatmaps of size ({heatmap_height}, {heatmap_width}), "
                f"but expected {self.sap_heatmap_size} (height, width)."
            )

    def estimate(self, img: RGBFrame) -> KeypointMap2D:
        """
        Run pose estimation and return keypoints in original input image coordinates.

        Parameters
        ----------
        img : RGBFrame
            Input image as a NumPy array with shape `(H, W, 3)` and dtype `uint8`,
            representing an RGB or BGR image (preprocessing handles both).

        Returns
        -------
        KeypointMap2D
            A dictionary mapping semantic keypoint names (e.g., `'nose'`, `'left_knee'`)
            to `Keypoint2D` instances with `(x, y)` expressed in **original image pixel coordinates**.
            Only keypoints with confidence >= `self._confidence_threshold` are included.

        Notes
        -----
        - This method assumes the model has already been validated to output the correct
        number of heatmaps for the configured keypoint format (validated in `__init__`).
        Therefore, no runtime shape validation is performed for performance reasons.

        - The internal Sapiens model operates on a fixed input resolution (768x1024) and
        produces heatmaps of fixed size (192x256). This implementation automatically scales
        the detected keypoint coordinates from the heatmap space to the original input image
        dimensions using simple proportional scaling. 
        This ensures that the returned keypoints can be directly overlaid on the input image
        without requiring additional post-processing by the user.
        
        - Keypoints with confidence below `self._confidence_threshold` are **excluded** from
        the returned dictionary. This behavior aligns with the configuration contract.
        """

        # Capture original image dimensions for coordinate scaling
        original_height, original_width = img.shape[:2]

        # Preprocess image: (H, W, 3) uint8 -> (1, 3, 768, 1024) float32 tensor
        tensor = self._preprocessor(img)

        # Move tensor to the configured device and run inference
        tensor = tensor.to(self._device)
        with torch.inference_mode():
            heatmaps: torch.Tensor = self._model(tensor)  # Shape: (1, K, 192, 256)

        # Convert heatmaps to CPU for efficient NumPy processing
        heatmaps_np: NDArray[np.float32] = heatmaps[0].cpu().numpy()  # Shape: (K, 192, 256)

        # Extract keypoints by locating maxima in each heatmap
        keypoints: KeypointMap2D = {}
        heatmap_width, heatmap_height = self.sap_heatmap_size

        for i, name in enumerate(self._keypoint_names):
            # np.unravel_index returns (row, col) = (y, x) in heatmap coordinates
            y_hm, x_hm = np.unravel_index(np.argmax(heatmaps_np[i]), heatmaps_np[i].shape)
            confidence = float(heatmaps_np[i, y_hm, x_hm])

            # Skip keypoints below confidence threshold
            if confidence < self._confidence_threshold:
                continue

            # Scale from heatmap space to original image space
            x_original = x_hm * (original_width / heatmap_width)
            y_original = y_hm * (original_height / heatmap_height)

            keypoints[name] = Keypoint2D(
                x=float(x_original),
                y=float(y_original),
                confidence=confidence
            )

        return keypoints

    def __call__(self, img: RGBFrame) -> KeypointMap2D:
        """
        Alias for `estimate`, enabling callable-style usage.

        Parameters
        ----------
        img : RGBFrame
            Input image (see `estimate` for details).

        Returns
        -------
        KeypointMap2D
            Keypoints (see `estimate` for details).
        """
        
        return self.estimate(img)