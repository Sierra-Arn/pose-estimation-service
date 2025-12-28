# app/rest/storage_endpoints/analysis_download.py
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
from app.rest.storage_endpoints.router import storage_router
from ..config import rest_config
from ...pickle_data import load_running_analysis_from_minio


@storage_router.get("/analysis/{video_id}/download", response_class=JSONResponse)
def download_analysis(video_id: str):
    """
    Retrieve the running analysis results as JSON for a given video ID.

    Loads the analysis from a pickle file stored under `<video_id>/<estimation_analysis_name>`,
    converts it to a dictionary, and returns it as a JSON response.

    Parameters
    ----------
    video_id : str
        UUID4 string identifying the uploaded video and its artifacts.

    Returns
    -------
    JSONResponse
        JSON representation of the VideoAnalysis NamedTuple.

    Raises
    ------
    HTTPException
        - 404 if the analysis file does not exist in storage.
        - 500 if an unexpected error occurs (e.g., storage unreachable, corrupted data).
    """

    storage_key = f"{video_id}/{rest_config.running_analysis_name}"

    try:
        analysis = load_running_analysis_from_minio(storage_key)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis results not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to access storage"
            ) from e
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load or parse analysis results"
        ) from e

    return JSONResponse(content=analysis._asdict())