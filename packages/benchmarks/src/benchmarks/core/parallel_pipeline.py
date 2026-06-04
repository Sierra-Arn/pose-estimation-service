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

# packages/benchmarks/src/benchmarks/core/parallel_pipeline.py
from typing import NamedTuple, Literal
from pathlib import Path
import time
import asyncio
import httpx
from scripts.quick_start.shared import ApiUrls, add_video_url
from . import (
    IngestResult, 
    TaskResult, 
    VideoMetadata,
    ingest_video_async, 
    submit_and_poll_task_async,
    get_video_metadata,
)
from .estimation_latency import ProcessingParams


class VisualizationParams(NamedTuple):
    """
    Container for visualization task parameters.
    
    Attributes
    ----------
    show_bbox : bool
        Toggle bounding box rendering in the output video.
    show_bbox_confidence : bool
        Toggle detection confidence score rendering.
    show_keypoints : bool
        Toggle 2D keypoint marker rendering.
    show_skeleton : bool
        Toggle skeletal connection rendering.
    crf : int
        Constant Rate Factor for x264 encoding (0-51).
    preset : str
        x264 encoding speed versus compression trade-off preset.
    batch_size : int
        Number of frames processed per encoding batch.
    """
    show_bbox: bool
    show_bbox_confidence: bool
    show_keypoints: bool
    show_skeleton: bool
    crf: int
    preset: Literal[
        "ultrafast", "superfast", "veryfast", "faster", "fast",
        "medium", "slow", "slower", "veryslow"
    ]
    batch_size: int


class VideoPipelineResult(NamedTuple):
    """
    Container for the results of a single video pipeline execution.
    
    Attributes
    ----------
    file_path : Path
        Path to the processed video file.
    file_size_mb : float
        Size of the video file in megabytes.
    video_metadata : VideoMetadata or None
        Metadata extracted from the API, or None if unavailable.
    ingest_result : IngestResult
        Result of the video ingestion request.
    estimation_result : TaskResult or None
        Result of the estimation task, or None if ingestion failed.
    visualization_result : TaskResult or None
        Result of the visualization task, or None if estimation failed.
    """
    file_path: Path
    file_size_mb: float
    video_metadata: VideoMetadata | None
    ingest_result: IngestResult
    estimation_result: TaskResult | None
    visualization_result: TaskResult | None


class ParallelPipelineResult(NamedTuple):
    """
    Container for the results of a parallel pipeline benchmark.
    
    Attributes
    ----------
    video_results : list of VideoPipelineResult
        Results for each processed video file.
    total_wall_clock_time_ms : float
        Total real time from start to finish of all parallel tasks.
    total_summed_time_ms : float
        Sum of all individual stage latencies across all videos.
    """
    video_results: list[VideoPipelineResult]
    total_wall_clock_time_ms: float
    total_summed_time_ms: float


async def process_single_video(
    client: httpx.AsyncClient,
    urls: ApiUrls,
    file_path: Path,
    est_params: dict,
    vis_params: dict
) -> VideoPipelineResult:
    """
    Process a single video through the complete pipeline asynchronously.
    
    Parameters
    ----------
    client : httpx.AsyncClient
        The asynchronous HTTP client instance.
    urls : ApiUrls
        NamedTuple containing all API endpoint URLs.
    file_path : Path
        Path to the video file to process.
    est_params : dict
        Dictionary containing estimation task parameters.
    vis_params : dict
        Dictionary containing visualization task parameters.
    
    Returns
    -------
    VideoPipelineResult
        A NamedTuple containing all results for this video.
    """
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    
    # Stage 1: Ingest
    ingest_result = await ingest_video_async(client, urls, file_path)
    
    if not ingest_result.video_id:
        return VideoPipelineResult(
            file_path=file_path,
            file_size_mb=file_size_mb,
            video_metadata=None,
            ingest_result=ingest_result,
            estimation_result=None,
            visualization_result=None
        )
    
    # Fetch video metadata
    video_metadata = None
    try:
        video_urls = add_video_url(urls, ingest_result.video_id)
        video_metadata = get_video_metadata(video_urls)
    except Exception:
        pass
    
    # Stage 2: Estimation
    est_params_with_id = {**est_params, "video_id": ingest_result.video_id}
    estimation_result = await submit_and_poll_task_async(
        client, urls, "estimation", est_params_with_id
    )
    
    if not estimation_result.success or not estimation_result.resource_id:
        return VideoPipelineResult(
            file_path=file_path,
            file_size_mb=file_size_mb,
            video_metadata=video_metadata,
            ingest_result=ingest_result,
            estimation_result=estimation_result,
            visualization_result=None
        )
    
    # Stage 3: Visualization
    vis_params_with_id = {**vis_params, "estimation_id": estimation_result.resource_id}
    visualization_result = await submit_and_poll_task_async(
        client, urls, "visualization", vis_params_with_id
    )
    
    return VideoPipelineResult(
        file_path=file_path,
        file_size_mb=file_size_mb,
        video_metadata=video_metadata,
        ingest_result=ingest_result,
        estimation_result=estimation_result,
        visualization_result=visualization_result
    )


async def execute_benchmark(
    urls: ApiUrls,
    video_files: list[Path],
    processing_params: ProcessingParams,
    visualization_params: VisualizationParams
) -> ParallelPipelineResult:
    """
    Execute the parallel pipeline benchmark for multiple videos.
    
    Each video is processed independently through the complete pipeline
    (ingest -> estimation -> visualization) in parallel with other videos.
    
    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing all API endpoint URLs.
    video_files : list of Path
        List of paths to video files to process.
    processing_params : ProcessingParams
        NamedTuple containing estimation parameters.
    visualization_params : VisualizationParams
        NamedTuple containing visualization parameters.
    
    Returns
    -------
    ParallelPipelineResult
        A NamedTuple containing all results and timing metrics.
    """
    est_params = {
        "target_width": processing_params.target_width,
        "target_height": processing_params.target_height,
        "target_fps": processing_params.target_fps,
        "skip_start_seconds": 0.0,
        "duration_seconds": processing_params.duration_seconds,
        "batch_size": processing_params.batch_size,
    }
    
    vis_params = {
        "show_bbox": visualization_params.show_bbox,
        "show_bbox_confidence": visualization_params.show_bbox_confidence,
        "show_keypoints": visualization_params.show_keypoints,
        "show_skeleton": visualization_params.show_skeleton,
        "crf": visualization_params.crf,
        "preset": visualization_params.preset,
        "batch_size": visualization_params.batch_size,
    }
    
    start_time = time.perf_counter()
    
    async with httpx.AsyncClient() as client:
        tasks = [
            process_single_video(client, urls, file_path, est_params, vis_params)
            for file_path in video_files
        ]
        video_results = await asyncio.gather(*tasks)
    
    total_wall_clock_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Calculate sum of all individual stage latencies
    total_summed_time_ms = 0.0
    for result in video_results:
        total_summed_time_ms += result.ingest_result.latency_ms
        if result.estimation_result:
            total_summed_time_ms += result.estimation_result.latency_ms
        if result.visualization_result:
            total_summed_time_ms += result.visualization_result.latency_ms
    
    return ParallelPipelineResult(
        video_results=list(video_results),
        total_wall_clock_time_ms=total_wall_clock_time_ms,
        total_summed_time_ms=total_summed_time_ms
    )