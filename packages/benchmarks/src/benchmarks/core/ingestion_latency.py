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

# packages/benchmarks/src/benchmarks/core/ingestion_latency.py
import time
from pathlib import Path
from typing import NamedTuple
import requests
from scripts.quick_start.shared import ApiUrls


class RequestResult(NamedTuple):
    """
    Container for the result of a synchronous HTTP POST request with latency measurement.
    
    Attributes
    ----------
    status_code : int
        The HTTP status code returned by the server.
    latency_ms : float
        The time taken to complete the request in milliseconds.
    message : str
        The response message, error detail, or a fallback description.
    video_id : int or None
        The unique identifier of the video if the request succeeded, else None.
    """
    status_code: int
    latency_ms: float
    message: str
    video_id: str | None


def send_request_and_measure_latency(
    urls: ApiUrls, 
    file_path: Path, 
    timeout: float = 60.0
) -> RequestResult:
    """
    Send a POST request with a file to the ingestion endpoint and measure the execution time.

    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing the ingest_url endpoint.
    file_path : Path
        Path to the file to be uploaded.
    timeout : float, optional
        Maximum number of seconds to wait for a response from the server.
        Default is 60.0.

    Returns
    -------
    RequestResult
        A NamedTuple containing the HTTP status code, latency in milliseconds, 
        the response message or error detail, and the video ID if successful.
    """
    start_time = time.perf_counter()
    
    try:
        with open(file_path, "rb") as f:
            response = requests.post(urls.ingest_url, files={"file": f}, timeout=timeout)
    except requests.exceptions.Timeout:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return RequestResult(
            status_code=408,
            latency_ms=duration_ms,
            message=f"Request timed out after {timeout} seconds",
            video_id=None
        )
    except requests.exceptions.RequestException as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return RequestResult(
            status_code=503,
            latency_ms=duration_ms,
            message=str(e),
            video_id=None
        )
        
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    video_id = None
    
    try:
        data = response.json()
        message = data.get("detail", "No detail provided")
        if response.status_code in (200, 201):
            video_id = data.get("id")
    except ValueError:
        message = "Success" if response.status_code < 400 else response.text[:100]
        
    return RequestResult(
        status_code=response.status_code,
        latency_ms=duration_ms,
        message=message,
        video_id=video_id
    )


class IngestionBenchmarkResult(NamedTuple):
    """
    Container for the results of a two-step ingestion benchmark.
    
    Attributes
    ----------
    first_request : RequestResult
        Result of the initial full ingestion request.
    second_request : RequestResult or None
        Result of the deduplication check request, or None if the first request failed.
    video_id : str or None
        The unique identifier of the video if the first request succeeded, else None.
    """
    first_request: RequestResult
    second_request: RequestResult | None
    video_id: str | None


def execute_benchmark(urls: ApiUrls, test_file: Path) -> IngestionBenchmarkResult:
    """
    Perform the two-step ingestion benchmark.

    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing the ingest_url endpoint.
    test_file : Path
        Path to the local video file.

    Returns
    -------
    IngestionBenchmarkResult
        A NamedTuple containing the results of the first and second requests,
        and the video ID if the first request was successful.
    """
    print("[info] sending first request (full ingestion)...")
    r1 = send_request_and_measure_latency(urls, test_file)
    
    if r1.status_code in (400, 500):
        print(f"[error] first request failed with status {r1.status_code}")
        return IngestionBenchmarkResult(
            first_request=r1,
            second_request=None,
            video_id=None
        )
        
    print("[info] sending second request (deduplication check)...")
    r2 = send_request_and_measure_latency(urls, test_file)
    
    return IngestionBenchmarkResult(
        first_request=r1,
        second_request=r2,
        video_id=r1.video_id
    )