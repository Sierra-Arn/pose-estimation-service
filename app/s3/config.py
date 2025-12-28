# app/s3/config.py
from typing import ClassVar
from pydantic import Field
from ..shared import BaseConfig


class MinIOConfig(BaseConfig):
    """
    Configuration schema for MinIO object storage.

    Attributes
    ----------
    host : str
        Hostname or IP address of the MinIO server. Default is `"127.0.0.1"`.
    external_port : int
        TCP port the server listens on. Must be in the range 1-65535.
        Default is `9000` (standard MinIO port).
    bucket_name : str
        Name of the MinIO bucket used for storing files.
        Default is `"data"`.
    root_username : str
        MinIO root username (acts as AWS access key).
        Default is `"minio_admin"`.
    root_password : str
        MinIO root password (acts as AWS secret key).
        Default is `"5up3r-53cr37-p455w0rd"`.

    Notes
    -----
    This class inherits from `app.shared.base_config.BaseConfig`.
    For details on configuration loading behavior, see its documentation.
    """

    env_prefix: ClassVar[str] = "MINIO_"

    host: str = "127.0.0.1"
    external_port: int = Field(9000, ge=1, le=65535)
    bucket_name: str = "data"
    root_username: str = "minio_admin"
    root_password: str = "5up3r-53cr37-p455w0rd"

    @property
    def connection_url(self) -> str:
        """
        Build MinIO connection URL from configuration settings.

        Returns
        -------
        str
            Complete MinIO connection URL in the format: http://host:port
        """

        return f"http://{self.host}:{self.external_port}"


# Initialize MinIO configuration singleton
# Since MinIO storage settings are static for the application's lifetime
# and any changes require a restart to take effect,
# it is safe and efficient to instantiate this configuration once at module level
# and reuse it throughout the application as a singleton.
minio_config = MinIOConfig()