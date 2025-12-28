# app/rest/ml_endpoints/video_request.py
import itertools
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
from app.rest.ml_endpoints.router import ml_router
from ..config import rest_config
from ..schemas import VideoRenderRequest
from ...s3 import files_service
from ...pickle_data import load_estimation_results_from_minio
from ...video import encode_and_upload_to_minio_streaming, render_annotated_frame, decode_from_minio_streaming


@ml_router.post("/render-video", response_class=JSONResponse)
def request_video(request: VideoRenderRequest):
    """
    Generate and save an annotated video with pose overlays.

    Given a `video_id`, this endpoint:
    1. Verifies that both input video and pose estimation results exist,
    2. Streams the original video frame-by-frame,
    3. Loads the corresponding keypoints for each frame,
    4. Renders annotations (bbox, keypoints, skeleton) onto each frame,
    5. Encodes the result as an MP4 and uploads it.

    Parameters
    ----------
    request : VideoRenderRequest
        - `video_id`: UUID4 of the video to annotate.
        - `fps`: Target frame rate (default: 30.0).
        - `crf`: Video quality (lower = better quality, default: 22).
        - Rendering flags: `show_bbox`, `show_keypoints`, etc.

    Returns
    -------
    JSONResponse
        Success message with video_id.

    Raises
    ------
    HTTPException
        - 404 if input video or pose results are missing.
        - 500 on decoding, rendering, or encoding errors.
    """
    video_id = request.video_id

    # Construct storage keys
    input_video_key = f"{video_id}/{rest_config.input_video_name}"
    estimations_key = f"{video_id}/{rest_config.estimation_results_name}"
    output_video_key = f"{video_id}/{rest_config.output_video_name}"

    # --- 1. Verify input video exists ---
    try:
        files_service.head_object(input_video_key)
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
                detail="Storage error (input video)"
            ) from e

    # --- 2. Verify pose estimation results exist ---
    try:
        files_service.head_object(estimations_key)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pose estimation results not found. Run /estimation first."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage error (pose results)"
            ) from e

    # --- 3. Load pose estimation results ---
    try:
        estimation_results_sequence = load_estimation_results_from_minio(storage_key=estimations_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load pose estimation results"
        ) from e

    # --- 4. Initialize raw frame stream ---
    raw_frame_gen = decode_from_minio_streaming(
        storage_key=input_video_key,
        expires=300,
        fps_target=request.fps
    )

    # --- 5. Extract first frame to get resolution ---
    try:
        first_frame = next(raw_frame_gen)
    except StopIteration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input video contains no frames"
        )

    height, width = first_frame.shape[:2]

    # Reconstruct full frame stream including the first frame
    full_raw_gen = itertools.chain([first_frame], raw_frame_gen)

    # --- 6. Annotated frame generator ---
    def annotated_frame_generator():
        for frame, estimation_result in zip(full_raw_gen, estimation_results_sequence):
            annotated = render_annotated_frame(
                frame=frame,
                keypoints=estimation_result.keypoints,
                bounding_box=estimation_result.bbox,
                show_bbox=request.show_bbox,
                show_keypoints=request.show_keypoints,
                show_confidence=request.show_confidence,
                show_skeleton=request.show_skeleton
            )
            yield annotated

    # --- 7. Encode and upload annotated video ---
    try:
        encode_and_upload_to_minio_streaming(
            frame_generator=annotated_frame_generator(),
            storage_key=output_video_key,
            width=width,
            height=height,
            fps_target=request.fps,
            crf=request.crf
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render or encode annotated video"
        ) from e

    return JSONResponse(
        content={
            "message": "Annotated video rendered and saved successfully",
            "video_id": video_id
        }
    )