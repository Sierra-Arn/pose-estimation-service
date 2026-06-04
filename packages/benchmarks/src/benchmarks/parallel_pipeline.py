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

# packages/benchmarks/src/benchmarks/parallel_pipeline.py
"""
Benchmark for parallel video processing through the complete pipeline.

Processes multiple videos concurrently, where each video independently goes through:
1. Video ingestion (upload and registration)
2. Pose estimation (GPU inference)
3. Visualization rendering (video overlay generation)

Each video starts processing immediately after ingestion completes, without waiting
for other videos. This demonstrates true parallel processing capabilities of the system.

Usage
-----
pixi run -e full python -m benchmarks.parallel_pipeline \
    --video-dir ./example-videos \
    --num-default-workers 1 \
    --num-inference-workers 2 \
    --target-width 1920 \
    --target-height 1080 \
    --target-fps 20.0 \
    --duration-seconds 10.0 \
    --batch-size 30 \
    --crf 20 \
    --preset medium
"""
import sys
import asyncio
from pathlib import Path
from scripts.quick_start.shared import (
    wait_for_server,
    start_infrastructure,
    get_api_urls,
    wait_for_server,
)
from .core import (
    get_cpu_name,
    get_cuda_env,
    parse_benchmark_args,
    start_services,
    stop_services,
)
from .core.estimation_latency import ProcessingParams
from .core.parallel_pipeline import (
    VisualizationParams,
    ParallelPipelineResult,
    execute_benchmark
)


def _print_results(
    target_url: str,
    num_default_workers: int,
    num_inference_workers: int,
    processing_params: ProcessingParams,
    visualization_params: VisualizationParams,
    benchmark_result: ParallelPipelineResult,
) -> None:
    """
    Format and print the parallel pipeline benchmark configuration and results.

    Parameters
    ----------
    target_url : str
        The base API URL.
    num_default_workers : int
        Number of default CPU worker processes running during the benchmark.
    num_inference_workers : int
        Number of inference GPU worker processes running during the benchmark.
    processing_params : ProcessingParams
        NamedTuple containing estimation parameters.
    visualization_params : VisualizationParams
        NamedTuple containing visualization parameters.
    benchmark_result : ParallelPipelineResult
        NamedTuple containing all video results and timing metrics.
    """
    cpu_name = get_cpu_name()
    cuda_env = get_cuda_env()
    requested_frames = int(processing_params.duration_seconds * processing_params.target_fps)

    print("\n⚙️  ===== System Configuration =====")
    print(f"Target URL:                     {target_url}")
    print(f"CPU Name:                       {cpu_name}")
    print(f"GPU Name:                       {cuda_env.gpu_name}")
    print(f"PyTorch Version:                {cuda_env.torch_version}")
    print(f"CUDA Version:                   {cuda_env.cuda_version}")
    print(f"Number of Servers:              1")
    print(f"Number of Default Workers:      {num_default_workers}")
    print(f"Number of Inference Workers:    {num_inference_workers}")
    
    print(f"\n📋 ===== Estimation Parameters =====")
    print(f"  Target Resolution:            {processing_params.target_width} x {processing_params.target_height}")
    print(f"  Target Duration:              {processing_params.duration_seconds:.2f} sec")
    print(f"  Target FPS:                   {processing_params.target_fps:.2f}")
    print(f"  Target Frames:                {requested_frames}")
    print(f"  Batch Size:                   {processing_params.batch_size}")
    
    print(f"\n🎨 ===== Visualization Parameters =====")
    print(f"  Show Bounding Boxes:          {visualization_params.show_bbox}")
    print(f"  Show BBox Confidence:         {visualization_params.show_bbox_confidence}")
    print(f"  Show Keypoints:               {visualization_params.show_keypoints}")
    print(f"  Show Skeleton:                {visualization_params.show_skeleton}")
    print(f"  CRF (Quality):                {visualization_params.crf}")
    print(f"  Encoding Preset:              {visualization_params.preset}")
    print(f"  Batch Size:                   {visualization_params.batch_size}")
    
    print(f"\n🎬 ===== Video Processing Results =====")
    
    for idx, video_result in enumerate(benchmark_result.video_results, 1):
        print(f"\n[Video {idx}] {video_result.file_path.name}")
        print(f"  File Size:                {video_result.file_size_mb:.4f} MB")
        
        if video_result.video_metadata:
            print(f"  Resolution:               {video_result.video_metadata.width} x {video_result.video_metadata.height}")
            print(f"  Duration:                 {video_result.video_metadata.duration_seconds:.2f} sec")
            print(f"  FPS:                      {video_result.video_metadata.fps:.2f}")
        
        ingest_time = video_result.ingest_result.latency_ms
        print(f"  Ingest Time:              {ingest_time:.2f} ms", end="")
        if not video_result.ingest_result.video_id:
            print(f" ❌ Failed: {video_result.ingest_result.error}")
        else:
            print(f" ✅")
        
        if video_result.estimation_result:
            est_time = video_result.estimation_result.latency_ms
            print(f"  Estimation Time:          {est_time:.2f} ms", end="")
            if video_result.estimation_result.success:
                print(f" ✅")
            else:
                print(f" ❌ Failed: {video_result.estimation_result.error_msg}")
        else:
            print(f"  Estimation Time:          None (skipped)")
        
        if video_result.visualization_result:
            vis_time = video_result.visualization_result.latency_ms
            print(f"  Visualization Time:       {vis_time:.2f} ms", end="")
            if video_result.visualization_result.success:
                print(f" ✅")
            else:
                print(f" ❌ Failed: {video_result.visualization_result.error_msg}")
        else:
            print(f"  Visualization Time:       None (skipped)")
    
    print(f"\n⏱️  ===== Performance Metrics =====")
    print(f"  Total Videos Processed:     {len(benchmark_result.video_results)}")
    print(f"  Wall-Clock Time:            {benchmark_result.total_wall_clock_time_ms:.2f} ms")
    print(f"  Summed Stage Times:         {benchmark_result.total_summed_time_ms:.2f} ms")
    
    if benchmark_result.total_wall_clock_time_ms > 0:
        parallelism_ratio = benchmark_result.total_summed_time_ms / benchmark_result.total_wall_clock_time_ms
        print(f"  Parallelism Ratio:          {parallelism_ratio:.2f}x")
        print(f"  (Ratio > 1.0 indicates effective parallel processing)")
    
    print("\n================================\n")


if __name__ == "__main__":
    args = parse_benchmark_args()
    
    required_args = [
        "video_dir",
        "num_default_workers", 
        "num_inference_workers",
        "target_width", 
        "target_height", 
        "target_fps", 
        "duration_seconds", 
        "batch_size", 
        "preset",
        "crf"
    ]
    for arg_name in required_args:
        if getattr(args, arg_name) is None:
            print(f"[error] --{arg_name.replace('_', '-')} is required for this benchmark.")
            sys.exit(1)
    
    video_dir = Path(args.video_dir).resolve()
    if not video_dir.exists() or not video_dir.is_dir():
        print(f"[error] Specified directory not found: {video_dir}")
        sys.exit(1)
    
    # Find all video files in directory
    video_extensions = {".mp4", ".mov", ".webm"}
    video_files = [f for f in video_dir.iterdir() if f.suffix.lower() in video_extensions]
    
    if not video_files:
        print(f"[error] No video files found in directory: {video_dir}")
        sys.exit(1)
    
    print(f"[info] Found {len(video_files)} video file(s) in {video_dir}")
    
    processing_params = ProcessingParams(
        target_width=args.target_width,
        target_height=args.target_height,
        target_fps=args.target_fps,
        duration_seconds=args.duration_seconds,
        batch_size=args.batch_size,
    )
    
    # Visualization parameters with defaults
    visualization_params = VisualizationParams(
        show_bbox=args.show_bbox,
        show_bbox_confidence=args.show_bbox_confidence,
        show_keypoints=args.show_keypoints,
        show_skeleton=args.show_skeleton,
        crf=args.crf,
        preset=args.preset,
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

        print("[info] system is healthy, starting parallel pipeline benchmark")
        
        benchmark_result = asyncio.run(
            execute_benchmark(urls, video_files, processing_params, visualization_params)
        )
        
        _print_results(
            target_url=urls.base_url,
            num_default_workers=args.num_default_workers,
            num_inference_workers=args.num_inference_workers,
            processing_params=processing_params,
            visualization_params=visualization_params,
            benchmark_result=benchmark_result,
        )
    finally:
        stop_services(processes)
        print("[info] benchmark script finished")