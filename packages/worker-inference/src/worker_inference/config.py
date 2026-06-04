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

# packages/worker-inference/src/worker_inference/config.py
from typing import ClassVar, Final
from ensam3d_inference import DeviceType
from base_lib import BaseConfig, LogLevel


class InferenceWorkerConfig(BaseConfig):
    """
    Configuration schema for the inference Celery worker process.

    Combines environment-supplied pipeline parameters with architectural
    constants that are fixed for the lifetime of the process. Pool,
    concurrency, and prefetch settings are hardcoded to solo/1/1 to ensure
    the single loaded model occupies GPU memory exclusively without
    contention or duplication across forked processes.

    Attributes
    ----------
    name : str
        Worker identity string used for routing and monitoring. Appears in
        Celery logs and worker lists. Default is "inference_worker@%n" where
        %n is expanded by Celery to the hostname at worker startup.
    model_path : str
        Local filesystem path to the model directory or a HuggingFace
        repository ID containing the pretrained pipeline weights.
        Default is "sam-3d-body-vith".
    model_device : DeviceType
        Device used for feature extraction, pose estimation, and all
        preprocessing output tensors consumed by the model.
        Default is "cuda".
    detector_model_path : str
        YOLO model name or local file path passed to the detector. If the
        weights are not found locally they are downloaded automatically
        from the Ultralytics asset registry. Default is "yolo26n.pt".
    detector_device : DeviceType
        Device used for YOLO-based human detection. Default is "cuda".
    log_level : LogLevel
        Minimum severity threshold for log message processing. Controls
        verbosity of worker lifecycle events and task execution diagnostics.
        Default is "INFO".
    _pool : str
        Celery worker pool implementation. Fixed to solo to run all tasks
        in the main process without forking, preserving the loaded model
        weights in a single memory space.
    _concurrency : str
        Number of concurrent worker processes or threads. Fixed to 1 to
        prevent multiple model instances from competing for GPU memory.
    _prefetch_multiplier : str
        Number of tasks fetched from the broker ahead of execution. Fixed
        to 1 to prevent a second task from occupying the broker slot while
        the worker is blocked on GPU inference.
    """

    env_prefix: ClassVar[str] = "WORKER_INFERENCE_"

    # == ENV-DEPENDENT (configurable via WORKER_INFERENCE_ prefixed env vars) ==
    name: str = "inference_worker@%n"
    model_path: str = "sam-3d-body-vith"
    model_device: DeviceType = "cuda"
    detector_model_path: str = "yolo26n.pt"
    detector_device: DeviceType = "cuda"
    log_level: LogLevel = "INFO"

    # ====== ARCHITECTURAL CONSTANTS (private, not configurable via env) ======
    _pool: Final[str] = "solo"
    _concurrency: Final[str] = "1"
    _prefetch_multiplier: Final[str] = "1"


inference_worker_config = InferenceWorkerConfig()