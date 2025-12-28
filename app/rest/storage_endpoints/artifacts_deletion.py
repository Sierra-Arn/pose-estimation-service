# app/rest/storage_endpoints/artifacts_deletion.py
from fastapi import status, HTTPException
from app.rest.storage_endpoints.router import storage_router
from ..config import rest_config
from ...s3 import files_service


@storage_router.delete("/artifacts/{video_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifacts(video_id: str) -> None:
    """
    Delete all artifacts associated with a previously uploaded video.

    The operation is idempotent: deleting a non-existent or partially missing
    video collection does not raise an error and results in a successful
    204 No Content response.

    Parameters
    ----------
    video_id : str
        UUID4 string that uniquely identifies the uploaded video and its artifacts.
        Must be a non-empty string.
    """

    # Construct storage keys using configured filenames
    input_video_key = f"{video_id}/{rest_config.input_video_name}"
    output_video_key = f"{video_id}/{rest_config.output_video_name}"
    estimation_results_key = f"{video_id}/{rest_config.estimation_results_name}"
    estimation_analysis_key = f"{video_id}/{rest_config.running_analysis_name}"

    # Delete all associated artifacts (idempotent per key)
    try:
        files_service.delete(input_video_key)
        files_service.delete(output_video_key)
        files_service.delete(estimation_results_key)
        files_service.delete(estimation_analysis_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video artifacts"
        ) from e

    # FastAPI returns 204 No Content automatically due to status_code and None return