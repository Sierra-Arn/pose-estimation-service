# app/s3/service.py
from io import BytesIO, IOBase
from botocore.exceptions import ClientError
from .client import get_sync_minio_session
from .config import minio_config


class FileService:
    """
    Synchronous service for managing file operations on a single S3-compatible storage bucket.

    This class encapsulates all interactions with object storage (e.g., MinIO) for a fixed bucket.
    Each method acquires a fresh storage client via a context manager, guaranteeing proper
    resource cleanup and thread safety. Input parameters are assumed to be valid and safe to use;
    no validation is performed by this service.

    Attributes
    ----------
    bucket_name : str
        The name of the bucket this service instance operates on.
    """

    def __init__(self, bucket_name: str):
        """
        Initialize the service with a target bucket.

        Parameters
        ----------
        bucket_name : str
            Name of the S3-compatible bucket to manage.
        """

        self.bucket_name = bucket_name

    def create_bucket(self) -> None:
        """
        Create the bucket defined in the MinIO configuration if it doesn't already exist.

        This method is safe to call multiple times — if the bucket already exists,
        no error is raised, and a message is printed instead.
        """
        try:
            with get_sync_minio_session() as client:
                client.create_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' created successfully.")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
                print(f"Bucket '{self.bucket_name}' already exists. Skipping creation.")
            else:
                # Re-raise if it's a different error (e.g., permissions, invalid name, etc.)
                raise

    def upload_fileobj(self, storage_key: str, fileobj: BytesIO | IOBase) -> None:
        """
        Upload a file-like object (e.g., BytesIO) to the bucket under the given key.

        Parameters
        ----------
        storage_key : str
            The key/path under which to store the object in the bucket.
        fileobj : file-like object (supports read())
            A binary stream (e.g., io.BytesIO) containing the data to upload.
        """

        with get_sync_minio_session() as client:
            client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=self.bucket_name,
                Key=storage_key
            )

    def head_object(self, storage_key: str) -> dict:
        """
        Retrieve metadata of an object without downloading its body.

        Parameters
        ----------
        storage_key : str
            Key of the object in the bucket.

        Returns
        -------
        dict
            Response metadata (e.g., ETag, Content-Length, Last-Modified) as a dictionary.

        Notes
        -----
        This method is primarily used to check whether an object exists in the bucket.
        """

        with get_sync_minio_session() as client:
            return client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )

    def download_as_bytes(self, storage_key: str) -> bytes:
        """
        Retrieve an object from the service's bucket and return its content as raw bytes.

        Parameters
        ----------
        storage_key : str
            Key of the object to retrieve from the bucket.

        Returns
        -------
        bytes
            Complete binary content of the object.

        Notes
        -----
        Loads the entire object into application memory. Suitable only for small files.
        """

        with get_sync_minio_session() as client:
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            try:
                return response['Body'].read()
            finally:
                # Ensure the underlying HTTP connection is released back to the pool
                response['Body'].close()

    def generate_presigned_url(self, storage_key: str, expires: int = 300) -> str:
        """
        Generate a presigned URL for temporary public access to a private object.

        Parameters
        ----------
        storage_key : str
            Key of the object in the bucket.
        expires : int, optional
            URL expiration time in seconds. Default is 300 (5 min).

        Returns
        -------
        str
            A temporary HTTP(S) URL that can be used to access the object.

        Notes
        -----
        Delegates data transfer directly to MinIO — no data passes through the application.
        Ideal for large files (e.g., videos) to preserve memory and bandwidth.
        """

        with get_sync_minio_session() as client:
            return client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': storage_key},
                ExpiresIn=expires
            )

    def delete(self, storage_key: str) -> None:
        """
        Delete an object from the service's bucket by its storage key.

        The operation is idempotent: deleting a non-existent object does not raise an error.

        Parameters
        ----------
        storage_key : str
            Key of the object to delete from the bucket.
        """
        
        with get_sync_minio_session() as client:
            client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )


# Initialize FileService singleton  
# Since the application uses a single, fixed S3-compatible bucket for all file operations  
# and the bucket name is determined at startup via static configuration,  
# it is safe, efficient, and semantically correct to instantiate a single FileService  
# at module level and reuse it globally throughout the application lifetime.
files_service = FileService(bucket_name=minio_config.bucket_name)