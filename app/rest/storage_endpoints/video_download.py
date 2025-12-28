# app/rest/storage_endpoints/video_download.py
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from botocore.exceptions import ClientError
from app.rest.storage_endpoints.router import storage_router
from ..config import rest_config
from ...s3 import files_service
from ...video import stream_video_from_presigned_url


@storage_router.get("/video/{video_id}/download", response_class=StreamingResponse)
def download_video(video_id: str):
    """
    Stream the annotated output video for a given video ID.

    Verifies the video exists, generates a presigned URL, and streams the file
    in chunks to the client with a fixed `Content-Type: video/mp4` header.

    Parameters
    ----------
    video_id : str
        UUID4 string identifying the uploaded video and its artifacts.

    Returns
    -------
    StreamingResponse
        A stream of the video file with `Content-Type: video/mp4`.

    Raises
    ------
    HTTPException
        - 404 if the video file does not exist in storage.
        - 500 if storage/backend errors occur during validation or URL generation.
    """
    
    storage_key = f"{video_id}/{rest_config.output_video_name}"

    # Step 1: Verify the object exists in storage
    try:
        files_service.head_object(storage_key)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output video not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage access error"
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify video existence"
        ) from e

    # Step 2: Generate presigned URL
    try:
        presigned_url = files_service.generate_presigned_url(storage_key, expires=300)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link"
        ) from e

    # Step 3: Return streaming response with fixed MIME type
    return StreamingResponse(
        stream_video_from_presigned_url(presigned_url),
        media_type="video/mp4"
    )