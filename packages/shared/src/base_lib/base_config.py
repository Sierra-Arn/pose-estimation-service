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

# packages/shared/src/base_lib/base_config.py
from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """
    Base configuration class for pydantic-settings integration.

    Subclasses inherit automatic resolution of settings from environment
    variables, including values loaded from a .env file. During instantiation
    configuration values are evaluated in strict precedence order: explicitly
    passed constructor arguments take highest priority, followed by environment
    variables matching the subclass prefix, with class-level field defaults
    serving as the final fallback.

    Subclasses must define a class-level env_prefix string to scope their
    environment variables. The configuration model is generated dynamically
    via __init_subclass__ to enforce UTF-8 encoding, case-insensitive matching,
    silent ignoring of unrecognized keys, and post-instantiation immutability.

    Notes
    -----
    Environment variable resolution ignores case. Extra keys outside the
    configured schema are discarded without warning. Instances are frozen
    after creation to guarantee runtime stability.
    """

    env_prefix: ClassVar[str]

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if "env_prefix" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must define 'env_prefix' as a class variable string "
                "to scope environment variables."
            )
        cls.model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
            frozen=True,
            env_prefix=cls.env_prefix,
        )