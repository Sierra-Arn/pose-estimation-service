# app/rest/ml_endpoints/analysis_request.py
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
from app.rest.ml_endpoints.router import ml_router
from ..config import rest_config
from ..schemas import RunningAnalysisRequest
from ...s3 import files_service
from ...running_analysis import analyze_full_video
from ...pickle_data import load_estimation_results_from_minio, save_running_analysis_to_minio


@ml_router.post("/analyze", response_class=JSONResponse)
def request_analysis(request: RunningAnalysisRequest):
    """
    Perform Running analysis on existing pose estimation results.

    Given a `video_id` and anatomical `side`, this endpoint:
    1. Verifies that pose estimation results exist,
    2. Loads the keypoints sequence,
    3. Runs full-video running analysis,
    4. Saves results.

    Parameters
    ----------
    request : RunningAnalysisRequest
        - `video_id`: UUID4 of the processed video.
        - `side`: Anatomical side of the body to analyze ('left' or 'right'). Default is `"right"`.

    Returns
    -------
    JSONResponse
        Success message with video_id.

    Raises
    ------
    HTTPException
        - 404 if pose estimation results are missing.
        - 500 on analysis or storage errors.
    """

    video_id = request.video_id
    side = request.side

    # Construct storage keys
    estimation_results_key = f"{video_id}/{rest_config.estimation_results_name}"
    analysis_key = f"{video_id}/{rest_config.running_analysis_name}"

    # --- 1. Verify pose estimation results exist ---
    try:
        files_service.head_object(estimation_results_key)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pose estimation results not found."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage access error"
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify pose estimation results"
        ) from e

    # --- 2. Load pose estimation results ---
    try:
        estimation_results_sequence = load_estimation_results_from_minio(storage_key=estimation_results_key)
        keypoints_sequence = [r.keypoints for r in estimation_results_sequence]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load pose estimation results"
        ) from e

    # --- 3. Run Running analysis ---
    try:
        analysis = analyze_full_video(keypoints_sequence=keypoints_sequence, side=side)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Running analysis failed"
        ) from e

    # --- 4. Save analysis to MinIO ---
    try:
        save_running_analysis_to_minio(analysis=analysis, storage_key=analysis_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save Running analysis"
        ) from e

    return JSONResponse(
        content={
            "message": "Running analysis completed successfully",
            "video_id": video_id
        }
    )