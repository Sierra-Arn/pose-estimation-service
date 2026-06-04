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

# packages/benchmarks/src/benchmarks/ingestion_latency.py
"""
Benchmark for the video ingestion endpoint latency and deduplication logic.

Sends the specified file to the ingestion endpoint twice. 
The first request triggers full validation, hashing, MinIO upload, and DB registration.
The second request hits the deduplication cache (SHA-256 match in DB), bypassing 
heavy I/O and returning the existing record instantly.

Usage
-----
pixi run -e full python -m benchmarks.ingestion_latency \
    --file-path example.mp4 \
    --num-default-workers 1 \
    --num-inference-workers 1
"""
import sys
from pathlib import Path
from scripts.quick_start.shared import (
    wait_for_server,
    start_infrastructure,
    get_api_urls,
    wait_for_server,
    add_video_url
)
from .core import (
    get_cpu_name,
    get_cuda_env,
    parse_benchmark_args,
    start_services,
    stop_services,
    get_video_metadata,
    VideoMetadata
)
from .core.ingestion_latency import execute_benchmark, IngestionBenchmarkResult


def _print_results(
    target_url: str,
    test_file: Path,
    video_metadata: VideoMetadata | None,
    benchmark_result: IngestionBenchmarkResult,
    num_default_workers: int,
    num_inference_workers: int,
) -> None:
    """
    Format and print the benchmark configuration and results to the console.

    Parameters
    ----------
    target_url : str
        The ingestion endpoint URL.
    test_file : Path
        Path to the tested video file.
    video_metadata : VideoMetadata or None
        NamedTuple containing width, height, fps, and duration_seconds from API.
    benchmark_result : IngestionBenchmarkResult
        NamedTuple containing the results of the first and second requests,
        and the video ID if the first request was successful.
    num_default_workers : int
        Number of default CPU worker processes running during the benchmark.
    num_inference_workers : int
        Number of inference GPU worker processes running during the benchmark.
    """
    file_size_mb = test_file.stat().st_size / (1024 * 1024)
    cpu_name = get_cpu_name()
    cuda_env = get_cuda_env()

    print("\n⚙️  ===== Configuration =====")
    print(f"Target URL:                     {target_url}")
    print(f"CPU Name:                       {cpu_name}")
    print(f"GPU Name:                       {cuda_env.gpu_name}")
    print(f"PyTorch Version:                {cuda_env.torch_version}")
    print(f"CUDA Version:                   {cuda_env.cuda_version}")
    print(f"Number of Servers:              1")
    print(f"Number of Default Workers:      {num_default_workers}")
    print(f"Number of Inference Workers:    {num_inference_workers}")
    print(f"File Name:                      {test_file.name}")
    print(f"File Size:                      {file_size_mb:.4f} MB")
    
    if video_metadata:
        print(f"Video Resolution:               {video_metadata.width} x {video_metadata.height}")
        print(f"Video Duration:                 {video_metadata.duration_seconds:.2f} sec")
        print(f"Video FPS:                      {video_metadata.fps:.2f}")
    else:
        print("Video Metadata:                  Not available (first request failed)")
    
    print()
    print("📊 ===== Benchmark Results =====")
    
    r1 = benchmark_result.first_request
    print(f"[1st Request] Status: {r1.status_code} | Latency: {r1.latency_ms:.2f} ms | Msg: {r1.message}")
    
    r2 = benchmark_result.second_request
    if r2 is not None:
        print(f"[2nd Request] Status: {r2.status_code} | Latency: {r2.latency_ms:.2f} ms | Msg: {r2.message}")
        if r1.latency_ms > 0 and r2.latency_ms > 0:
            speedup = r1.latency_ms / r2.latency_ms
            print(f"Speedup (Dedup):         {speedup:.2f}x faster")
    else:
        print("[2nd Request] Skipped due to error in 1st request.")
        
    print("================================\n")


if __name__ == "__main__":

    args = parse_benchmark_args()
    required_args = ["file_path", "num_default_workers", "num_inference_workers"]
    for arg_name in required_args:
        if getattr(args, arg_name) is None:
            print(f"[error] --{arg_name.replace('_', '-')} is required for this benchmark.")
            sys.exit(1)
    
    test_file = Path(args.file_path).resolve()
    if not test_file.exists():
        print(f"[error] Specified file not found: {test_file}")
        sys.exit(1)

    start_infrastructure()
    urls = get_api_urls()
    processes = start_services(
        num_default=args.num_default_workers,
        num_inference=args.num_inference_workers
    )

    try:
        if not wait_for_server(urls):
            print("[error] server failed to become healthy")
            sys.exit(1)

        wait_for_server(urls)

        print("[info] system is healthy, starting benchmark")
        results = execute_benchmark(urls, test_file)
        
        video_metadata = None
        if results.video_id:
            try:
                video_urls = add_video_url(urls=urls, video_id=results.video_id)
                video_metadata = get_video_metadata(video_urls)
            except Exception as e:
                print(f"[warn] failed to fetch video metadata: {e}")
        
        _print_results(
            target_url=urls.ingest_url,
            test_file=test_file,
            video_metadata=video_metadata,
            benchmark_result=results,
            num_default_workers=args.num_default_workers,
            num_inference_workers=args.num_inference_workers,
        )
    finally:
        stop_services(processes)
        print("[info] benchmark script finished")