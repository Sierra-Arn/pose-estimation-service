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

# app/workers/default/main.py
from .config import default_worker_config
from ..task_queue.config import celery_config
from ..task_queue.instance import celery_app


def main() -> None:
    """
    Launch the default Celery worker using environment-based configuration.

    The worker consumes exclusively from the default queue and handles
    CPU-bound background operations such as visualization rendering and
    metadata extraction. Pool strategy and concurrency are configurable
    via WORKER_DEFAULT_ prefixed environment variables since the default
    worker operates without GPU memory constraints.

    Returns
    -------
    None
        Blocks indefinitely while the Celery worker processes tasks from the
        default queue. Terminates only on external SIGTERM or SIGKILL.
    """

    worker_argv = [
        "worker",
        "--hostname", default_worker_config.name,
        "--queues", celery_config.queue_name_default,
        "--pool", default_worker_config.pool,
        "--concurrency", str(default_worker_config.concurrency),
        "--prefetch-multiplier", str(default_worker_config.prefetch_multiplier),
        "--loglevel", default_worker_config.log_level,
    ]

    celery_app.worker_main(argv=worker_argv)


if __name__ == "__main__":
    main()