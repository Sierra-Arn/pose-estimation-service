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

# packages/server/src/server/main.py
import uvicorn
from .config import server_config
from .logger import setup_logging


def main() -> None:
    """
    Apply structured logging and launch the FastAPI application under Uvicorn.

    Configures the process-local logging hierarchy via setup_logging before
    handing control to Uvicorn. The server binds to the host and port resolved
    from ServerConfig and runs synchronously until an external SIGTERM or
    SIGKILL is received.

    Returns
    -------
    None
        Blocks indefinitely while Uvicorn serves incoming HTTP requests.
        Terminates only on external SIGTERM or SIGKILL.
    """
    setup_logging()

    uvicorn.run(
        "server.app:create_app",
        factory=True,
        host=server_config.host,
        port=server_config.port,
        log_config=None,
        log_level=None,
    )


if __name__ == "__main__":
    main()