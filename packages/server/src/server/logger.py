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

# packages/server/src/server/logger.py
import logging.config
from base_lib import base_logging_config
from .config import server_config


def setup_logging() -> None:
    """
    Configure structured JSON logging for the server process.

    Applies thresholds from ServerConfig to the root logger and all
    Uvicorn sub-loggers. All handlers emit to stdout for downstream 
    log aggregation.

    Returns
    -------
    None
        Configures the global logging module in-place.
    """
    config = base_logging_config(server_config.log_level)
    config["loggers"] = {
        "uvicorn": {"handlers": ["console"], "level": server_config.log_level, "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": server_config.log_level, "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": server_config.log_level, "propagate": False},
    }
    logging.config.dictConfig(config)