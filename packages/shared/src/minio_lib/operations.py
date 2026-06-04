# Copyright (c) 2026 Ilya Snegov (aka Sierra Arn)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# packages/shared/src/minio_lib/operations.py
from .utils import get_sync_client, get_async_client
from .config import minio_config


class StorageOperations:
    """
    Low-level S3 operations for interacting with object storage.

    This class is a pure I/O layer: it performs no validation and applies no business rules.
    Since the service operates against a single bucket, bucket configuration is resolved
    internally from minio_config rather than passed explicitly by the caller.

    All methods are static: the class carries no instance state and exists purely
    as a logical namespace for S3-related I/O operations.
    """

    @staticmethod
    async def upload_bytes(
        storage_key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        """
        Upload raw bytes to the bucket under the specified storage key.

        Parameters
        ----------
        storage_key : str
            Destination key for the object in the bucket.
        data : bytes
            Raw binary payload to upload.
        content_type : str
            MIME type to attach to the object metadata, defining how
            downstream consumers and the storage console interpret
            the uploaded payload.

        Raises
        ------
        ClientError
            If the upload fails due to permissions, connectivity, or quota issues.
        """
        async with get_async_client() as client:
            await client.put_object(
                Bucket=minio_config.user_bucket_name,
                Key=storage_key,
                Body=data,
                ContentType=content_type,
            )

    @staticmethod
    def upload_file_sync(
        storage_key: str,
        file_path: str,
        content_type: str,
    ) -> None:
        """
        Upload a local file to the bucket under the specified storage key
        using synchronous I/O suitable for Celery worker contexts.

        Parameters
        ----------
        storage_key : str
            Destination key for the object in the bucket.
        file_path : str
            Path to the local file to be uploaded.
        content_type : str
            MIME type to attach to the object metadata, defining how
            downstream consumers and the storage console interpret
            the uploaded payload.

        Raises
        ------
        ClientError
            If the upload fails due to permissions, connectivity, or quota issues.
        """
        client = get_sync_client()
        client.upload_file(
            Filename=file_path,
            Bucket=minio_config.user_bucket_name,
            Key=storage_key,
            ExtraArgs={"ContentType": content_type},
        )

    @staticmethod
    async def download_bytes_with_type(storage_key: str) -> tuple[bytes, str]:
        """
        Download the full content of an object from the bucket as raw bytes
        along with its MIME content type metadata.

        Parameters
        ----------
        storage_key : str
            Key of the object to download.

        Returns
        -------
        tuple of bytes and str
            Two-element tuple where the first item is the raw binary payload
            of the requested object and the second item is the MIME content
            type stored in the object metadata (for example, video/mp4 or
            application/json). Falls back to application/octet-stream when
            the content type metadata is absent from the object.

        Raises
        ------
        ClientError
            If the object does not exist or access is denied.
        """
        async with get_async_client() as client:
            response = await client.get_object(
                Bucket=minio_config.user_bucket_name,
                Key=storage_key,
            )
            body = await response["Body"].read()
            content_type = response.get("ContentType")
            return body, content_type

    @staticmethod
    def download_bytes_sync(storage_key: str) -> bytes:
        """
        Download the full content of an object from the bucket as raw bytes using synchronous I/O.

        Parameters
        ----------
        storage_key : str
            Key of the object to download.

        Returns
        -------
        bytes
            Raw binary payload of the requested object.

        Raises
        ------
        ClientError
            If the object does not exist or access is denied.
        """
        client = get_sync_client()
        response = client.get_object(
            Bucket=minio_config.user_bucket_name,
            Key=storage_key,
        )
        return response["Body"].read()

    @staticmethod
    async def delete(storage_key: str) -> None:
        """
        Delete an object from the bucket by its storage key.

        The operation is idempotent: deleting a non-existent object does not raise an error
        consistent with S3 semantics.

        Parameters
        ----------
        storage_key : str
            Key of the object to delete.

        Raises
        ------
        ClientError
            If the delete operation fails due to permissions or connectivity issues.
        """
        async with get_async_client() as client:
            await client.delete_object(Bucket=minio_config.user_bucket_name, Key=storage_key)

    @staticmethod
    async def delete_objects_batch(storage_keys: list[str]) -> None:
        """
        Delete multiple objects from the bucket in a single batched request.

        Uses the S3 DeleteObjects API to remove up to 1000 objects per call.
        Keys are automatically chunked if the input list exceeds the service limit.
        The operation performs deletion without collecting individual failure
        metadata. Network, permission, or configuration errors are raised
        immediately as ClientError.

        Parameters
        ----------
        storage_keys : list of str
            Object keys to delete from the bucket.

        Raises
        ------
        ClientError
            If the batch request fails due to connectivity, permissions,
            or invalid bucket configuration.
        """
        if not storage_keys:
            return

        chunk_size = 1000

        for i in range(0, len(storage_keys), chunk_size):
            chunk = storage_keys[i:i + chunk_size]
            delete_payload = {"Objects": [{"Key": k} for k in chunk]}

            async with get_async_client() as client:
                await client.delete_objects(
                    Bucket=minio_config.user_bucket_name,
                    Delete=delete_payload,
                )

    @staticmethod
    def generate_presigned_get_url(storage_key: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL for downloading an object from the bucket.

        Creates a time-limited URL that grants temporary read access to the
        specified object without requiring AWS credentials. The URL can be
        shared with clients or embedded in API responses for direct download
        from object storage.

        Parameters
        ----------
        storage_key : str
            Key of the object to generate a download URL for.
        expires : int, optional
            URL validity duration in seconds. Default is 3600.

        Returns
        -------
        str
            Presigned URL string valid for the specified duration.
        """
        client = get_sync_client()
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": minio_config.user_bucket_name,
                "Key": storage_key,
            },
            ExpiresIn=expires,
        )