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

# app/workers/inference/tasks/run_ensam3d/output_uploader.py
from pathlib import Path
from ensam3d_inference import PipelineOutput
from ....task_infra.tensors_io import save_pipeline_output
from .....shared.minio import StorageOperations


def upload_pipeline_output_to_minio(
    pipeline_output: PipelineOutput,
    storage_key: str,
) -> str:
    """
    Serialize pipeline output to safetensors and upload to MinIO via temporary file.

    Writes inference results to a local temporary file to avoid holding large
    tensor archives in memory, then streams the file to object storage using
    the synchronous upload operation. The temporary file is guaranteed to be
    removed after upload completion or failure.

    Parameters
    ----------
    pipeline_output : PipelineOutput
        Nested inference results containing tensors and metadata.
    storage_key : str
        Destination object key in the configured MinIO bucket.

    Returns
    -------
    str
        Confirmed storage_key of the uploaded result archive.

    Raises
    ------
    ValueError
        If pipeline_output is empty or invalid for serialization.
    RuntimeError
        If safetensors serialization or the MinIO upload fails.
    """
    tmp_path: Path | None = None
    try:
        tmp_path = save_pipeline_output(pipeline_output)
        StorageOperations.upload_file_sync(storage_key, str(tmp_path))
        return storage_key
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()