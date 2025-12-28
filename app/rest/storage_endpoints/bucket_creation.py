# app/rest/storage_endpoints/bucket_creation.py
from fastapi import HTTPException, status
from app.rest.storage_endpoints.router import storage_router
from ...s3 import files_service


@storage_router.post("/bucket/create", response_model=dict)
def create_bucket() -> dict:
    """
    Create the storage bucket (if it does not already exist) 
    used for video uploads and processing artifacts.

    Returns
    -------
    dict
        A JSON-serializable dictionary containing:
        - `"message"` (str): A success message confirming bucket creation attempt.

    Raises
    ------
    HTTPException
        - 500 error if the bucket creation fails.
    """

    try:
        files_service.create_bucket()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create storage bucket: {str(e)}"
        )

    return {"message": "Storage bucket already exists or has been created."}