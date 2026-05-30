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

# app/workers/inference/main.py
from ensam3d_inference import Pipeline
from . import _state
from .config import inference_worker_config
from ..task_queue.config import celery_config
from ..task_queue.instance import celery_app


def get_pipeline() -> Pipeline:
    """
    Return the pre-initialized inference pipeline for the current process.

    Provides tasks with access to the eagerly loaded inference engine.
    Raises a descriptive error if called before the worker startup sequence
    has completed.

    Returns
    -------
    Pipeline
        Loaded inference engine ready for synchronous execution on the
        current process.

    Raises
    ------
    RuntimeError
        Raised if the pipeline was not initialized during worker startup,
        indicating a misconfiguration or premature task dispatch.
    """
    if _state.pipeline is None:
        raise RuntimeError(
            "Inference pipeline not initialized. "
            "Ensure main() executed successfully before task dispatch."
        )
    return _state.pipeline


def main() -> None:
    """
    Eagerly initialize the inference pipeline and launch the Celery worker.

    The pipeline is loaded before entering the Celery worker loop to ensure
    fail-fast behavior on configuration errors and to eliminate cold-start
    latency for the first inference request. The worker consumes exclusively
    from the inference queue with solo pool and concurrency of 1 to ensure
    the loaded model weights occupy GPU memory without contention.
    Configuration is resolved from WORKER_INFERENCE_ prefixed environment
    variables via InferenceWorkerConfig.

    Returns
    -------
    None
        Blocks indefinitely while the Celery worker processes tasks from the
        inference queue. Terminates only on external SIGTERM or SIGKILL.
    """

    _state.pipeline = Pipeline(
        model_path=inference_worker_config.model_path,
        model_device=inference_worker_config.model_device,
        detector_device=inference_worker_config.detector_device,
        detector_model_path=inference_worker_config.detector_model_path,
    )

    worker_argv = [
        "worker",
        "--hostname", inference_worker_config.name,
        "--queues", celery_config.queue_name_inference,
        "--pool", inference_worker_config._pool,
        "--concurrency", inference_worker_config._concurrency,
        "--prefetch-multiplier", inference_worker_config._prefetch_multiplier,
        "--loglevel", inference_worker_config.log_level,
    ]

    celery_app.worker_main(argv=worker_argv)


if __name__ == "__main__":
    main()