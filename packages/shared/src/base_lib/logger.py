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

# packages/shared/src/base_lib/logger.py
from enum import StrEnum


class LogLevel(StrEnum):
    """
    Valid logging severity thresholds for all process-scoped log configurations.

    Maps to the standard Python logging level names accepted by logging.config
    dictConfig and the logging module itself.

    Attributes
    ----------
    DEBUG : LogLevel
        Finest granularity; includes diagnostic traces and internal state.
    INFO : LogLevel
        Routine operational events confirming expected behavior.
    WARNING : LogLevel
        Recoverable anomalies that do not interrupt normal execution.
    ERROR : LogLevel
        Failures requiring attention that degrade or block functionality.
    CRITICAL : LogLevel
        Severe failures causing process termination or data loss.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def base_logging_config(root_level: LogLevel) -> dict:
    """
    Build a minimal dictConfig skeleton with a single JSON stdout handler.

    Returns a configuration dict suitable for extension by process-specific
    setup functions. The root logger threshold is set to root_level; all
    framework loggers are left unconfigured and inherit from root unless
    the caller extends the loggers block.

    Parameters
    ----------
    root_level : LogLevel
        Minimum severity threshold for the root logger.

    Returns
    -------
    dict
        Partial dictConfig structure with version, formatters, handlers,
        and root configured. The loggers key is an empty dict ready for
        extension.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(process)s %(thread)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {
            "handlers": ["console"],
            "level": root_level,
        },
        "loggers": {},
    }