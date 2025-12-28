# app/human_pose_estimator/__init__.py
from .human_detector import HumanDetector, HumanDetectorConfig
from .pose_estimator import PoseEstimator, PoseEstimatorConfig
from .types import RGBFrame, Keypoint2D, PoseEstimationResult2D


class HumanPoseEstimator2D:
    """
    End-to-end human pose estimation pipeline that combines detection and 2D pose.

    The pipeline performs the following steps:
    1. Detects the person in the full image using YOLO.
    2. Crops the bounding box region containing the person.
    3. Runs a Sapiens-based pose estimator on the cropped region.
    4. Translates the 2D keypoints from cropped coordinates to the original image coordinate system.
    5. Returns 2D keypoints with (x, y) in original image pixels and confidence.

    Attributes
    ----------
    detector : HumanDetector
        Instance of the YOLO-based human detector that localizes a person in the input frame.
        Returns a bounding box in original image coordinates.
    pose_estimator : PoseEstimator
        Instance of the Sapiens-based pose estimator that predicts human keypoints
        **in the pixel coordinates of its input image** (i.e., the cropped region).
    """

    def __init__(
        self,
        human_detector_config: HumanDetectorConfig | None = None,
        pose_estimator_config: PoseEstimatorConfig | None = None,
    ):
        """
        Initialize the pose estimation pipeline with configurations for detection and pose.

        Parameters
        ----------
        human_detector_config : HumanDetectorConfig, optional
            Configuration for the human detection module. If not provided, a default
            instance of `HumanDetectorConfig` is created and used.
        pose_estimator_config : PoseEstimatorConfig, optional
            Configuration for the pose estimation module. If not provided, a default
            instance of `PoseEstimatorConfig` is created and used.
        """

        # Use provided configs or instantiate defaults
        detector_cfg = human_detector_config or HumanDetectorConfig()
        pose_estimator_cfg = pose_estimator_config or PoseEstimatorConfig()

        # Initialize subcomponents
        self.detector = HumanDetector(detector_cfg)
        self.pose_estimator = PoseEstimator(pose_estimator_cfg)

    def estimate(self, frame: RGBFrame) -> PoseEstimationResult2D:
        """
        Estimate human pose and bounding box in the original image coordinates.

        Parameters
        ----------
        frame : RGBFrame
            Input image as a NumPy array with shape `(H, W, 3)` and dtype `uint8`,
            in either RGB or BGR format (color space is handled internally).

        Returns
        -------
        PoseEstimationResult2D
            A named tuple with two fields:
            - `bbox`: `(x1, y1, x2, y2)` bounding box in original image coordinates,
              or `None` if no person is detected.
            - `keypoints`: dictionary mapping keypoint names to `Keypoint2D` objects
              with `(x, y, confidence)`, where:
                - `x`, `y` are in **original image pixel coordinates**,
                - `confidence` is the detection score.

        Notes
        -----
        The pose estimator returns results in the coordinate system of its input image
        (i.e., the cropped region).
        """

        bbox = self.detector(frame)
        if bbox is None:
            return PoseEstimationResult2D(bbox=None, keypoints={})

        cropped = frame[bbox.y1:bbox.y2, bbox.x1:bbox.x2]

        # Run pose estimation on the cropped image region
        keypoints_crop = self.pose_estimator(cropped)

        # Initialize result dictionary
        keypoints_original = {}

        # Process each detected keypoint
        for name, kp in keypoints_crop.items():
            # kp.x, kp.y are in cropped image pixel coordinates
            x_orig = kp.x + bbox.x1
            y_orig = kp.y + bbox.y1

            # Store 2D keypoint
            keypoints_original[name] = Keypoint2D(
                x=float(x_orig),
                y=float(y_orig),
                confidence=kp.confidence
            )

        return PoseEstimationResult2D(
            bbox=bbox,
            keypoints=keypoints_original
        )

    def __call__(self, img: RGBFrame) -> PoseEstimationResult2D:
        """
        Alias for `estimate`, enabling callable-style usage.

        Parameters
        ----------
        img : RGBFrame
            Input image (see `estimate` for details).

        Returns
        -------
        PoseEstimationResult2D
            Bounding box and 2D keypoints in original image coordinates.
        """

        return self.estimate(img)