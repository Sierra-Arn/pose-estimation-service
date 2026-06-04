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

# packages/benchmarks/src/benchmarks/core/__init__.py
import os
import subprocess
import argparse
import time
from pathlib import Path
from typing import NamedTuple, Literal
import signal
import requests
import torch
import asyncio
import httpx
from scripts.quick_start.shared import run, ApiUrls


def parse_benchmark_args() -> argparse.Namespace:
    """
    Parse command line arguments for all benchmark scripts.

    All arguments are optional by default. Individual scripts should validate 
    that the specific arguments they require have been provided.

    Returns
    -------
    argparse.Namespace
        Parsed arguments containing any combination of video directory, 
        file path, worker counts, and processing parameters.
    """
    parser = argparse.ArgumentParser(
        description="Unified argument parser for benchmark scripts."
    )
    
    # File and directory inputs
    parser.add_argument(
        "--video-dir", 
        type=str, 
        default=None, 
        help="Directory containing video files."
    )
    parser.add_argument(
        "--file-path", 
        type=str, 
        default=None, 
        help="Path to the local video file to upload."
    )
    
    # Worker configuration
    parser.add_argument(
        "--num-default-workers", 
        type=int, 
        default=None, 
        help="Number of default CPU workers to spawn."
    )
    parser.add_argument(
        "--num-inference-workers", 
        type=int, 
        default=None, 
        help="Number of inference GPU workers to spawn."
    )
    
    # Processing parameters
    parser.add_argument(
        "--target-width", 
        type=int, 
        default=None, 
        help="Target frame width."
    )
    parser.add_argument(
        "--target-height", 
        type=int, 
        default=None, 
        help="Target frame height."
    )
    parser.add_argument(
        "--target-fps", 
        type=float, 
        default=None, 
        help="Target frame rate."
    )
    parser.add_argument(
        "--duration-seconds", 
        type=float, 
        default=None, 
        help="Duration of the segment to process."
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=None, 
        help="Frames per inference batch."
    )
    
    # Visualization parameters
    parser.add_argument(
        "--show-bbox", 
        action=argparse.BooleanOptionalAction, 
        default=False,
        help="Toggle bounding box rendering."
    )
    parser.add_argument(
        "--show-bbox-confidence", 
        action=argparse.BooleanOptionalAction, 
        default=False,
        help="Toggle detection confidence score rendering."
    )
    parser.add_argument(
        "--show-keypoints", 
        action=argparse.BooleanOptionalAction, 
        default=True,
        help="Toggle 2D keypoint marker rendering."
    )
    parser.add_argument(
        "--show-skeleton", 
        action=argparse.BooleanOptionalAction, 
        default=True,
        help="Toggle skeletal connection rendering."
    )
    parser.add_argument(
        "--crf", 
        type=int, 
        default=None, 
        help="x264 Constant Rate Factor for quality control (0-51)."
    )
    parser.add_argument(
        "--preset", 
        type=str, 
        default=None, 
        choices=[
            "ultrafast", "superfast", "veryfast", "faster", "fast", 
            "medium", "slow", "slower", "veryslow"
        ],
        help="x264 encoding speed versus compression preset."
    )
    return parser.parse_args()


def get_cpu_name() -> str:
    """
    Retrieve the full brand name of the CPU on Linux systems.

    Returns
    -------
    str
        The CPU name, or a fallback string if it cannot be determined.
    """
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":")[1].strip()
    except FileNotFoundError:
        pass
        
    return "Unknown CPU"


class CudaEnvInfo(NamedTuple):
    """
    Container for CUDA and PyTorch environment information.
    
    Attributes
    ----------
    gpu_name : str
        The name of the primary CUDA GPU, or a fallback string if unavailable.
    torch_version : str
        The installed version of PyTorch.
    cuda_version : str
        The CUDA version PyTorch was built with, or "N/A" if unavailable.
    """
    gpu_name: str
    torch_version: str
    cuda_version: str


def get_cuda_env() -> CudaEnvInfo:
    """
    Retrieve CUDA environment information using PyTorch.

    Returns
    -------
    CudaEnvInfo
        A NamedTuple containing the GPU name, PyTorch version, and CUDA version.
        Fallback strings are provided if CUDA is not available or an error occurs.
    """
    try:
        torch_version = torch.__version__
        cuda_version = torch.version.cuda or "N/A"
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
        else:
            gpu_name = "No CUDA GPU available"
            
        return CudaEnvInfo(
            gpu_name=gpu_name,
            torch_version=torch_version,
            cuda_version=cuda_version
        )
    except Exception:
        return CudaEnvInfo(
            gpu_name="Error retrieving GPU info",
            torch_version="Unknown",
            cuda_version="Unknown"
        )


def start_services(num_default: int = 1, num_inference: int = 1, verbose: bool = True) -> list[subprocess.Popen]:
    """
    Launch the API server and background worker processes.

    Parameters
    ----------
    num_default : int, optional
        Number of default CPU workers to spawn. Default is 1.
    num_inference : int, optional
        Number of inference GPU workers to spawn. Default is 1.
    verbose : bool, optional
        If True, prints informational messages. Default is True.

    Returns
    -------
    list of subprocess.Popen
        List of running process handles for later termination.
    """
    if verbose:
        print("[info] starting server and workers")
    
    processes = []
    commands = [["just", "server"]]
    
    for _ in range(num_default):
        commands.append(["just", "worker-default"])
    for _ in range(num_inference):
        commands.append(["just", "worker-inference"])
        
    for cmd in commands:
        p = subprocess.Popen(
            cmd, 
            preexec_fn=os.setsid,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(p)
        
    return processes


def stop_services(processes: list, verbose: bool = True) -> None:
    """
    Terminate all running service processes and tear down Docker containers.

    Parameters
    ----------
    processes : list of subprocess.Popen
        List of process handles to terminate.
    verbose : bool, optional
        If True, prints informational messages. Default is True.
    """
    if verbose:
        print("[info] shutting down all services")
        
    for p in processes:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
            
    run(["just", "docker-local-down"], verbose=verbose)


class VideoMetadata(NamedTuple):
    """
    Container for extracted video metadata.
    
    Attributes
    ----------
    width : int
        Frame width in pixels.
    height : int
        Frame height in pixels.
    fps : float
        Nominal frame rate of the video source.
    duration_seconds : float
        Total playback duration in seconds.
    """
    width: int
    height: int
    fps: float
    duration_seconds: float


def get_video_metadata(urls: ApiUrls) -> VideoMetadata:
    """
    Fetch video metadata from the API and extract key dimensions and duration.

    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing the video_url endpoint.

    Returns
    -------
    VideoMetadata
        A NamedTuple containing width, height, fps, and duration_seconds.

    Raises
    ------
    ValueError
        If the video_url is not provided in the urls object.
    RuntimeError
        If the HTTP request fails or returns a non-200 status code.
    """
    if not urls.video_url:
        raise ValueError("video_url is not set in the provided ApiUrls object")

    response = requests.get(urls.video_url, timeout=10)
    
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch video metadata. Status code: {response.status_code}, "
            f"Response: {response.text}"
        )
        
    data = response.json()
    
    return VideoMetadata(
        width=int(data["width"]),
        height=int(data["height"]),
        fps=float(data["fps"]),
        duration_seconds=float(data["duration_seconds"])
    )


class IngestResult(NamedTuple):
    """
    Container for the result of an asynchronous video ingestion request.
    
    Attributes
    ----------
    video_id : str or None
        The unique identifier of the ingested video, or None if the request failed.
    latency_ms : float
        The time taken to complete the request in milliseconds.
    error : str or None
        Error message if the request failed, or None if successful.
    """
    video_id: str | None
    latency_ms: float
    error: str | None


class TaskResult(NamedTuple):
    """
    Container for the result of an asynchronous task submission and polling.
    
    Attributes
    ----------
    success : bool
        True if the task completed successfully, False otherwise.
    resource_id : str or None
        The resulting resource ID if the task succeeded, None otherwise.
    latency_ms : float
        Total time from submission to completion in milliseconds.
    error_msg : str or None
        Error description if the task failed, None if successful.
    """
    success: bool
    resource_id: str | None
    latency_ms: float
    error_msg: str | None


async def ingest_video_async(
    client: httpx.AsyncClient,
    urls: ApiUrls,
    file_path: Path,
    timeout: float = 60.0
) -> IngestResult:
    """
    Asynchronously upload a video file to the ingestion endpoint.

    Parameters
    ----------
    client : httpx.AsyncClient
        The asynchronous HTTP client instance for connection pooling.
    urls : ApiUrls
        NamedTuple containing the ingest_url endpoint.
    file_path : Path
        Path to the local video file.
    timeout : float, optional
        Maximum number of seconds to wait for the server response.
        Default is 60.0.

    Returns
    -------
    IngestResult
        A NamedTuple containing the video ID, latency in milliseconds, 
        and an error message if the request failed.
    """
    start_time = time.perf_counter()
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "video/mp4")}
            response = await client.post(urls.ingest_url, files=files, timeout=timeout)
            
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        if response.status_code in (200, 201):
            video_id = response.json().get("id")
            return IngestResult(video_id=video_id, latency_ms=latency_ms, error=None)
        else:
            return IngestResult(video_id=None, latency_ms=latency_ms, error=response.text)
            
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return IngestResult(video_id=None, latency_ms=latency_ms, error=str(e))


async def submit_and_poll_task_async(
    client: httpx.AsyncClient,
    urls: ApiUrls,
    submit_type: Literal["estimation", "visualization"],
    params: dict,
    poll_interval: float = 1.0,
    timeout: float = 300.0
) -> TaskResult:
    """
    Asynchronously submit a task and poll its status until completion.

    Parameters
    ----------
    client : httpx.AsyncClient
        The asynchronous HTTP client instance for connection pooling.
    urls : ApiUrls
        NamedTuple containing all API endpoint URLs.
    submit_type : Literal["estimation", "visualization"]
        The type of task to submit. Determines which endpoint URL to use.
    params : dict
        Dictionary containing the task submission parameters.
    poll_interval : float, optional
        Number of seconds to wait between polling attempts. Default is 1.0.
    timeout : float, optional
        Maximum total time in seconds to wait for the task to complete.
        Default is 300.0.

    Returns
    -------
    TaskResult
        A NamedTuple containing success status, resource ID, latency in milliseconds,
        and an error message if the task failed.
    """
    submit_url = urls.estimation_submit_url if submit_type == "estimation" else urls.visualization_submit_url
    
    start_time = time.perf_counter()
    
    try:
        submit_resp = await client.post(submit_url, json=params, timeout=10.0)
        
        if submit_resp.status_code >= 400:
            duration_ms = (time.perf_counter() - start_time) * 1000
            try:
                msg = submit_resp.json().get("detail", "No detail provided")
            except ValueError:
                msg = submit_resp.text[:100]
            return TaskResult(success=False, resource_id=None, latency_ms=duration_ms, error_msg=msg)

        task_id = submit_resp.json().get("task_id")
        task_url = f"{urls.tasks_base_url}{task_id}/"
        
        while True:
            if time.perf_counter() - start_time > timeout:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return TaskResult(
                    success=False, 
                    resource_id=None, 
                    latency_ms=duration_ms, 
                    error_msg=f"Polling timeout exceeded ({timeout}s)"
                )
                
            await asyncio.sleep(poll_interval)
            
            task_resp = await client.get(task_url, timeout=10.0)
            
            if task_resp.status_code == 200:
                task_data = task_resp.json()
                status = task_data.get("status")
                
                if status in ("SUCCESS", "FAILURE", "REVOKED"):
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    if status == "SUCCESS":
                        resource_id = task_data.get("result", {}).get("resource_id")
                        return TaskResult(success=True, resource_id=resource_id, latency_ms=duration_ms, error_msg=None)
                    else:
                        error_detail = task_data.get("result")
                        return TaskResult(success=False, resource_id=None, latency_ms=duration_ms, error_msg=f"Failed: {error_detail}")
                        
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return TaskResult(success=False, resource_id=None, latency_ms=duration_ms, error_msg=str(e))