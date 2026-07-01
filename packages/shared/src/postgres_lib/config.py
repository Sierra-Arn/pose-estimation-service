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

# packages/shared/src/postgres_lib/config.py
from typing import ClassVar, Final
from urllib.parse import quote_plus
from pydantic import Field
from base_lib import BaseConfig


class PostgresConfig(BaseConfig):
    """
    Configuration schema for PostgreSQL database connectivity.

    Stores connection parameters for accessing a PostgreSQL instance via
    SQLAlchemy. All fields support resolution from environment variables
    prefixed with POSTGRES_ following the BaseConfig precedence rules.
    The sync_database_url and async_database_url properties assemble
    complete connection URIs for synchronous migrations and asynchronous
    application runtime respectively.

    Attributes
    ----------
    host : str
        Hostname or IP address of the PostgreSQL server endpoint.
        Default is "127.0.0.1".
    port : int
        TCP port for the PostgreSQL service; validated to lie within the
        standard 16-bit range. Default is 5432.
    user_name : str
        Database user name for authentication.
    user_password : str
        Database user password; treated as sensitive data.
    user_db_name : str
        Target database name for connection.
    _echo : bool
        Controls SQL statement logging to stdout; enabled for development
        debugging, disabled in production. Default is False.
    _autocommit : bool
        Controls automatic transaction commit in SQLAlchemy sessions;
        explicit commit calls are required when disabled. Default is False.
    _autoflush : bool
        Controls automatic flush of pending ORM changes before queries;
        manual flushing gives full control over side effects when disabled.
        Default is False.
    _expire_on_commit : bool
        Determines whether ORM objects are expired immediately after
        transaction commit; disabled to retain attribute access post-commit.
        Default is False.
    database_url : str
        Read-only property assembling the PostgreSQL connection URI with the
        psycopg (version 3) driver. The URL is mode-agnostic — the psycopg dialect
        backs both synchronous and asynchronous engines — so the engine constructor
        that consumes it (create_engine vs create_async_engine), not the URL,
        selects the mode.
    """

    env_prefix: ClassVar[str] = "POSTGRES_"

    # ========== ENV-DEPENDENT (configurable via POSTGRES_ prefixed env vars) ==========
    host: str = "127.0.0.1"
    port: int = Field(default=5432, ge=1, le=65535)
    user_name: str
    user_password: str
    user_db_name: str

    # ========== ARCHITECTURAL CONSTANTS (private, not configurable via env) ==========
    _echo: Final[bool] = False
    _autocommit: Final[bool] = False
    _autoflush: Final[bool] = False
    _expire_on_commit: Final[bool] = False

    @property
    def database_url(self) -> str:
        """
        Build the PostgreSQL connection URL from configuration settings.

        Uses the psycopg (version 3) driver, whose SQLAlchemy dialect
        serves both synchronous and asynchronous engines. Whether a connection 
        is sync or async is determined by the engine constructor used, not by the URL, 
        so a single URL is shared by Alembic migrations and the application runtime alike.

        Returns
        -------
        str
            Complete PostgreSQL connection URI in the format
            postgresql+psycopg://username:password@host:port/db_name
        """
        return (
            f"postgresql+psycopg://{self.user_name}:{quote_plus(self.user_password)}"
            f"@{self.host}:{self.port}/{self.user_db_name}"
        )


postgres_config = PostgresConfig()