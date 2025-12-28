# app/rest/ml_endpoints/estimation_request.py
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
from app.rest.ml_endpoints.router import ml_router
from ..config import rest_config
from ..schemas import PoseEstimationRequest
from ...s3 import files_service
from ...video.input import decode_from_minio_streaming
from ...human_pose_estimator import HumanPoseEstimator2D
from ...pickle_data import save_estimation_results_to_minio


@ml_router.post("/estimate", response_class=JSONResponse)
def request_estimation(request: PoseEstimationRequest):
    """
    Trigger 2D human pose estimation on an uploaded video.

    Accepts a JSON body with `video_id` and `fps`. The endpoint:
    1. Checks that the input video exists,
    2. Streams and decodes it at the specified frame rate,
    3. Runs 2D pose estimation frame-by-frame,
    4. Collects all keypoints,
    5. Saves results.

    Parameters
    ----------
    request : PoseEstimationRequest
        - `video_id`: UUID4 of the uploaded video.
        - `fps`: Target frame rate for processing (default: 30.0).

    Returns
    -------
    JSONResponse
        Success message with video_id.

    Raises
    ------
    HTTPException
        - 404 if input video is missing.
        - 500 on processing or storage errors.
    """

    video_id = request.video_id
    fps_target = request.fps

    # Construct storage keys
    video_key = f"{video_id}/{rest_config.input_video_name}"
    estimation_results_key = f"{video_id}/{rest_config.estimation_results_name}"

    # --- 1. Verify input video exists ---
    try:
        files_service.head_object(video_key)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Input video not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage access error"
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify input video"
        ) from e

    # --- 2. Initialize raw frame stream ---
    raw_frame_gen = decode_from_minio_streaming(
        storage_key=video_key,
        expires=300,
        fps_target=fps_target
    )

    # --- 3. Initialize pose estimator ---
    human_pose_estimator = HumanPoseEstimator2D()

    # --- 4. Run estimation ---
    estimation_results_sequence = []
    try:
        for frame in raw_frame_gen:
            result = human_pose_estimator(frame)
            estimation_results_sequence.append(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pose estimation failed during frame processing"
        ) from e

    # --- 5. Save results ---
    try:
        save_estimation_results_to_minio(
            estimation_results=estimation_results_sequence,
            storage_key=estimation_results_key
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save pose estimation results"
        ) from e

    return JSONResponse(
        content={
            "message": "Pose estimation completed successfully",
            "video_id": video_id
        }
    )