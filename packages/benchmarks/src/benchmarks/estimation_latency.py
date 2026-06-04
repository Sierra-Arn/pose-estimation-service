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

# packages/benchmarks/src/benchmarks/estimation_latency.py
"""
Benchmark for the estimation task latency and worker deduplication logic.

Submits the same estimation task twice for an ingested video.
The first request triggers full GPU inference and processing.
The second request hits the deduplication cache, bypassing heavy computation
and returning the existing result instantly.

Note: Worker counts and processing parameters must be explicitly specified 
to ensure reproducible benchmark conditions.

Usage
-----
pixi run -e full python -m benchmarks.estimation_latency \
    --file-path example.mp4 \
    --num-default-workers 1 \
    --num-inference-workers 1 \
    --target-width 1920 \
    --target-height 1080 \
    --target-fps 20.0 \
    --duration-seconds 20.0 \
    --batch-size 30
"""
import sys
import asyncio
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
from .core.estimation_latency import (
    ProcessingParams,
    EstimationBenchmarkResult,
    execute_benchmark
)


def _print_results(
    target_url: str,
    test_file: Path,
    processing_params: ProcessingParams,
    video_metadata: VideoMetadata | None,
    benchmark_result: EstimationBenchmarkResult,
    num_default_workers: int,
    num_inference_workers: int,
) -> None:
    """
    Format and print the benchmark configuration and results to the console.

    Parameters
    ----------
    target_url : str
        The estimation submission endpoint URL.
    test_file : Path
        Path to the tested video file.
    processing_params : ProcessingParams
        NamedTuple containing video processing parameters.
    video_metadata : VideoMetadata or None
        NamedTuple containing width, height, fps, and duration_seconds from API,
        or None if unavailable.
    benchmark_result : EstimationBenchmarkResult
        NamedTuple containing ingestion and task results.
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
        print(f"\n[Original Video]")
        print(f"  Resolution:                   {video_metadata.width} x {video_metadata.height}")
        print(f"  Duration:                     {video_metadata.duration_seconds:.2f} sec")
        print(f"  FPS:                          {video_metadata.fps:.2f}")
    else:
        print(f"\n[Original Video]")
        print(f"  Metadata:                     Not available")
    
    print(f"\n[Processing Params]")
    print(f"  Target Resolution:                {processing_params.target_width} x {processing_params.target_height}")
    print(f"  Target Duration:                  {processing_params.duration_seconds:.2f} sec")
    print(f"  Target FPS:                       {processing_params.target_fps:.2f}")
    print(f"  Batch Size:                       {processing_params.batch_size}")
    
    print("\n📊 ===== Benchmark Results =====")
    
    first_msg = "Success" if benchmark_result.first_task.success else benchmark_result.first_task.error_msg
    print(f"[1st Request] Success: {benchmark_result.first_task.success} | "
          f"Latency: {benchmark_result.first_task.latency_ms:.2f} ms | Msg: {first_msg}")
    
    if benchmark_result.second_task:
        second_msg = "Success" if benchmark_result.second_task.success else benchmark_result.second_task.error_msg
        print(f"[2nd Request] Success: {benchmark_result.second_task.success} | "
              f"Latency: {benchmark_result.second_task.latency_ms:.2f} ms | Msg: {second_msg}")
        
        if (benchmark_result.first_task.latency_ms > 0 
                and benchmark_result.second_task.latency_ms > 0):
            speedup = benchmark_result.first_task.latency_ms / benchmark_result.second_task.latency_ms
            print(f"Speedup (Dedup):         {speedup:.2f}x faster")
    else:
        print("[2nd Request] Skipped due to error in 1st request.")
        
    print("================================\n")


if __name__ == "__main__":
    args = parse_benchmark_args()
    
    required_args = [
        "file_path", 
        "num_default_workers", 
        "num_inference_workers",
        "target_width", 
        "target_height", 
        "target_fps", 
        "duration_seconds", 
        "batch_size"
    ]
    for arg_name in required_args:
        if getattr(args, arg_name) is None:
            print(f"[error] --{arg_name.replace('_', '-')} is required for this benchmark.")
            sys.exit(1)
    
    test_file = Path(args.file_path).resolve()
    if not test_file.exists():
        print(f"[error] Specified file not found: {test_file}")
        sys.exit(1)

    processing_params = ProcessingParams(
        target_width=args.target_width,
        target_height=args.target_height,
        target_fps=args.target_fps,
        duration_seconds=args.duration_seconds,
        batch_size=args.batch_size,
    )

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
        
        benchmark_result = asyncio.run(
            execute_benchmark(urls, test_file, processing_params)
        )
        
        video_metadata = None
        if benchmark_result.video_id:
            try:
                video_urls = add_video_url(urls=urls, video_id=benchmark_result.video_id)
                video_metadata = get_video_metadata(video_urls)
            except Exception as e:
                print(f"[warn] failed to fetch video metadata: {e}")
        
        _print_results(
            target_url=urls.estimation_submit_url,
            test_file=test_file,
            processing_params=processing_params,
            video_metadata=video_metadata,
            benchmark_result=benchmark_result,
            num_default_workers=args.num_default_workers,
            num_inference_workers=args.num_inference_workers,
        )
    finally:
        stop_services(processes)
        print("[info] benchmark script finished")