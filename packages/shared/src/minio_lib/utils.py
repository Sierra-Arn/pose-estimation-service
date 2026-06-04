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

# packages/shared/src/minio_lib/utils.py
import boto3
import aioboto3
from .config import minio_config


def get_sync_client() -> boto3.client:
    """
    Create and return a new synchronous S3-compatible boto3 client.

    Configures the client with endpoint, credentials, and connection
    parameters from the shared MinIO configuration. SSL verification
    is disabled to match the development deployment profile.

    Returns
    -------
    boto3.client
        Fully configured S3 client instance ready for immediate use
        in blocking code paths.
    """
    
    return boto3.client(
        service_name="s3",
        endpoint_url=minio_config.connection_url,
        aws_access_key_id=minio_config.user_name,
        aws_secret_access_key=minio_config.user_password,
        region_name="us-east-1",
        use_ssl=False,
        verify=False,
    )


def get_async_client() -> aioboto3.Session.client:
    """
    Create and return a new asynchronous S3-compatible aioboto3 client.

    Returns an async context manager that yields a configured client
    when entered with `async with`. Credentials and connection
    parameters are sourced from the shared MinIO configuration.
    SSL verification is disabled to match the development deployment
    profile.

    Returns
    -------
    aioboto3.Session.client
        Async context manager yielding a fully configured S3 client
        for use in non-blocking code paths.
    """
    
    session = aioboto3.Session()
    return session.client(
        service_name="s3",
        endpoint_url=minio_config.connection_url,
        aws_access_key_id=minio_config.user_name,
        aws_secret_access_key=minio_config.user_password,
        region_name="us-east-1",
        use_ssl=False,
        verify=False,
    )