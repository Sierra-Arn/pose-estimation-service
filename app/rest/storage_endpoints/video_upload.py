# app/rest/storage_endpoints/video_upload.py
import mimetypes
import uuid
from fastapi import UploadFile, File, status, HTTPException
from app.rest.storage_endpoints.router import storage_router
from ..config import rest_config
from ...s3 import files_service


ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/avi",
    "video/quicktime", # .mov
    "video/webm",
}


@storage_router.post("/video/upload", response_model=dict)
def upload_video(file: UploadFile = File(...)) -> dict:
    """
    Upload a video file and assign it a unique identifier.

    Accepts a multipart/form-data video upload, validates its MIME type using
    the filename (via `mimetypes`), generates a new UUID, and stores the file
    in the configured S3-compatible backend under `<video_id>/<input_video_name>`.

    The returned `video_uuid` can be used in subsequent API calls for analysis,
    results retrieval, or cleanup.

    Parameters
    ----------
    file : UploadFile
        The uploaded video file provided via HTTP multipart form data.
        Must have a filename with a video-associated extension.

    Returns
    -------
    dict
        A JSON-serializable dictionary containing:
        - `"message"` (str): Confirmation message.
        - `"video_uuid"` (str): UUID4 string that uniquely identifies this video.

    Raises
    ------
    HTTPException
        - 400 if the filename does not correspond to a known video MIME type.
        - 500 if the upload to storage fails.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename"
        )

    # Guess MIME type from filename (not content)
    mime_type, _ = mimetypes.guess_type(file.filename)

    if mime_type is None or mime_type not in ALLOWED_VIDEO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File must be a video. Detected MIME type: {mime_type}. "
                   f"Allowed types: {sorted(ALLOWED_VIDEO_MIME_TYPES)}"
        )

    video_uuid = str(uuid.uuid4())
    video_key = f"{video_uuid}/{rest_config.input_video_name}"

    try:
        files_service.upload_fileobj(storage_key=video_key, fileobj=file.file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload video to storage"
        ) from e

    return {
        "message": "Video uploaded successfully",
        "video_uuid": video_uuid
    }