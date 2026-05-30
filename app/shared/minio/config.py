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

# app/shared/minio/config.py
from typing import ClassVar
from pydantic import Field
from ..base_config import BaseConfig


class MinIOConfig(BaseConfig):
    """
    Configuration schema for MinIO object storage connectivity.

    Stores connection parameters for accessing a MinIO S3-compatible
    object storage instance. All fields support resolution from environment
    variables prefixed with MINIO_ following the BaseConfig precedence rules.

    Attributes
    ----------
    host : str
        Hostname or IP address of the MinIO server endpoint.
        Default is "127.0.0.1".
    port : int
        TCP port for the MinIO service; validated to lie within the
        standard 16-bit range. Default is 9000.
    user_bucket_name : str
        Target bucket identifier for object read and write operations.
        Default is "ensam3d-data".
    user_name : str
        App user access key used as the AWS access key equivalent.
    user_password : str
        App user secret key used as the AWS secret key equivalent.
    connection_url : str
        Read-only property assembling the full HTTP endpoint URL from
        host and port.
    """

    env_prefix: ClassVar[str] = "MINIO_"

    host: str = "127.0.0.1"
    port: int = Field(9000, ge=1, le=65535)
    user_bucket_name: str = "ensam3d-data"
    user_name: str
    user_password: str

    @property
    def connection_url(self) -> str:
        """
        Build MinIO connection URL from configuration settings.

        Returns
        -------
        str
            Complete MinIO connection URL in the format: http://host:port
        """
        return f"http://{self.host}:{self.port}"


minio_config = MinIOConfig()