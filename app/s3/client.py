# app/s3/client.py
from typing import Generator
from contextlib import contextmanager
import boto3
from .config import minio_config


@contextmanager
def get_sync_minio_session() -> Generator[boto3.client, None, None]:
    """
    Synchronous context manager for safe and automatic MinIO client lifecycle management.

    Provides a scoped S3-compatible client that is:
    1. Instantiated upon entry using application-wide MinIO credentials and endpoint,
    2. Yielded to the calling code block for S3 operations (e.g., upload, download, delete),
    3. Automatically discarded upon exit (no explicit cleanup needed, as boto3 clients
    are stateless and connection pooling is managed internally).

    Yields
    ------
    boto3.client
    A fully configured, ready-to-use synchronous MinIO (S3) client.

    Notes
    -----
    - boto3 clients are thread-safe and manage their own connection pools,
    so explicit closing is unnecessary. The context manager primarily serves
    to encapsulate client creation logic and enforce consistent configuration.
    - The client is created dynamically at runtime via boto3's factory function.
    As a result, static type checkers (e.g., mypy, Pylance) may not
    recognize its methods or attributes, leading to "unresolved attribute"
    warnings. This is expected and safe to ignore in S3-compatible usage.
    """

    client = boto3.client(
        service_name="s3",
        endpoint_url=minio_config.connection_url,
        aws_access_key_id=minio_config.root_username,
        aws_secret_access_key=minio_config.root_password,
        region_name="us-east-1",  # Required by S3 API, MinIO ignores it
        use_ssl=False,
        verify=False,
    )
    try:
        yield client
    finally:
        pass