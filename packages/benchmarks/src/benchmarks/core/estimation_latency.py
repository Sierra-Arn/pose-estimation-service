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

# packages/benchmarks/src/benchmarks/core/estimation_latency.py
from typing import NamedTuple
import httpx
from pathlib import Path
from scripts.quick_start.shared import ApiUrls
from . import IngestResult, TaskResult, ingest_video_async, submit_and_poll_task_async


class ProcessingParams(NamedTuple):
    """
    Container for video processing parameters.
    
    Attributes
    ----------
    target_width : int
        Target frame width for processing.
    target_height : int
        Target frame height for processing.
    target_fps : float
        Target frame rate for processing.
    duration_seconds : float
        Duration of the video segment to process.
    batch_size : int
        Number of frames per inference batch.
    """
    target_width: int
    target_height: int
    target_fps: float
    duration_seconds: float
    batch_size: int


class EstimationBenchmarkResult(NamedTuple):
    """
    Container for the results of a two-step estimation benchmark.
    
    Attributes
    ----------
    ingest_result : IngestResult
        Result of the initial video ingestion request.
    first_task : TaskResult
        Result of the first estimation task (full GPU execution).
    second_task : TaskResult or None
        Result of the second estimation task (deduplication check), 
        or None if the first task failed.
    video_id : str or None
        The unique identifier of the video if ingestion succeeded, else None.
    """
    ingest_result: IngestResult
    first_task: TaskResult
    second_task: TaskResult | None
    video_id: str | None


async def execute_benchmark(
    urls: ApiUrls, 
    test_file: Path, 
    processing_params: ProcessingParams
) -> EstimationBenchmarkResult:
    """
    Execute the full estimation benchmark pipeline asynchronously.

    Ingests a video, then submits the same estimation task twice.
    The first submission triggers full GPU inference; the second
    is expected to hit the deduplication cache and return instantly.

    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing all API endpoint URLs.
    test_file : Path
        Path to the local video file.
    processing_params : ProcessingParams
        NamedTuple containing video processing parameters.

    Returns
    -------
    EstimationBenchmarkResult
        A NamedTuple containing the ingestion result, first task result, 
        second task result (if applicable), and the video ID.
    """
    async with httpx.AsyncClient() as client:
        print("[info] ingesting video...")
        ingest_result = await ingest_video_async(client, urls, test_file)
        
        if not ingest_result.video_id:
            print(f"[error] ingestion failed: {ingest_result.error}")
            return EstimationBenchmarkResult(
                ingest_result=ingest_result,
                first_task=TaskResult(success=False, resource_id=None, latency_ms=0.0, error_msg="Ingest failed"),
                second_task=None,
                video_id=None
            )
        
        video_id = ingest_result.video_id
        print(f"[info] video ingested successfully, ID: {video_id}")
        
        est_params = {
            "video_id": video_id,
            "target_width": processing_params.target_width,
            "target_height": processing_params.target_height,
            "target_fps": processing_params.target_fps,
            "skip_start_seconds": 0.0,
            "duration_seconds": processing_params.duration_seconds,
            "batch_size": processing_params.batch_size,
        }
        
        print("[info] submitting first estimation task (full GPU execution)...")
        first_result = await submit_and_poll_task_async(
            client, urls, "estimation", est_params
        )
        
        if not first_result.success:
            print(f"[error] first estimation failed: {first_result.error_msg}")
            return EstimationBenchmarkResult(
                ingest_result=ingest_result,
                first_task=first_result,
                second_task=None,
                video_id=video_id
            )
        
        print("[info] submitting second estimation task (deduplication check)...")
        second_result = await submit_and_poll_task_async(
            client, urls, "estimation", est_params
        )
        
        return EstimationBenchmarkResult(
            ingest_result=ingest_result,
            first_task=first_result,
            second_task=second_result,
            video_id=video_id
        )