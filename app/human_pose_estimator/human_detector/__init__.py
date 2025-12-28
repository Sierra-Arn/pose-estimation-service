# app/human_pose_estimator/human_detector/__init__.py
import numpy as np
from numpy.typing import NDArray
from ultralytics import YOLO
from ultralytics.engine.results import Results
from .config import HumanDetectorConfig
from ..types import RGBFrame, BBox


class HumanDetector:
    """
    A YOLO-based human detector that returns a single person bounding box per image.

    Attributes
    ----------
    _model : ultralytics.YOLO
        Pre-loaded YOLO object detection model instance. The model is initialized
        from the weights file specified in the provided configuration.
    _confidence_threshold : float
        Confidence threshold for detection filtering. Detections with confidence
        below this value are discarded. Loaded from the provided configuration.
    _person_class_id : int
        The fixed COCO class ID for the 'person' category (always 0).
        This attribute is not configurable because the detector is specialized for **human detection only**.

    Notes
    -----
    For simplicity, it currently returns the first detected person;
    this logic can be extended in the future to select a specific individual
    (e.g., by size, position, or tracking ID).
    """

    def __init__(self, config: HumanDetectorConfig):
        """
        Initialize the detector using the provided configuration.

        Parameters
        ----------
        config : HumanDetectorConfig
            Configuration object specifying model path and confidence threshold.
        """

        self._model = YOLO(config.model_path)
        self._confidence_threshold = config.confidence_threshold
        self._person_class_id = 0

    def detect(self, img: RGBFrame) -> BBox | None:
        """
        Detect the person in the input image and return their bounding box.

        Parameters
        ----------
        img : RGBFrame
            Input image as a NumPy array with shape `(H, W, 3)` and dtype `uint8`,
            in RGB format.

        Returns
        -------
        PersonDetectionBoxes
            Array of shape `(1, 4)` containing the bounding box `[x1, y1, x2, y2]` 
            if a person is detected, or an empty array of shape `(0, 4)` otherwise.
        """

        # Run inference 
        # (Yolo model returns a list of Results objects, where each element corresponds to one input image; 
        # it is always a list, even for a single image)
        results: list[Results] = self._model(img, conf=self._confidence_threshold)
        pred: Results = results[0]

        # Extract detection boxes as NumPy array: (x1, y1, x2, y2, conf, cls)
        detections: NDArray[np.float32] = pred.boxes.data.cpu().numpy()

        # Filter by person class ID
        person_mask = detections[:, -1] == self._person_class_id
        person_detections = detections[person_mask]

        if person_detections.size == 0:
            return None

        # Take only the first detected person
        x1, y1, x2, y2 = person_detections[0, :4]  # Shape: (4,)
        h, w = img.shape[:2]

        # Clip bounding box coordinates to image boundaries
        x1 = int(np.clip(x1, 0, w))
        y1 = int(np.clip(y1, 0, h))
        x2 = int(np.clip(x2, 0, w))
        y2 = int(np.clip(y2, 0, h))

        if x2 <= x1 or y2 <= y1:
            return None

        return BBox(x1, y1, x2, y2)


    def __call__(self, img: RGBFrame) -> BBox | None:
        """
        Alias for `detect`.

        Parameters
        ----------
        img : RGBFrame
            Input image (see `detect` for details).

        Returns
        -------
        PersonDetectionBoxes
            Bounding box of the detected person (see `detect` for details).
        """

        return self.detect(img)