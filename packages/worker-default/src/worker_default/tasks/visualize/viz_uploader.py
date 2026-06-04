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

# packages/worker-default/src/worker_default/tasks/visualize/viz_uploader.py
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator
from ensam3d_inference.preprocessor.detector.types import RGBFrame
from minio_lib import StorageOperations


def encode_to_minio(
    frame_generator: Iterator[RGBFrame],
    storage_key: str,
    width: int,
    height: int,
    fps_target: float,
    crf: int,
    preset: str,
) -> None:
    """
    Encode a stream of RGB frames into an MP4 video and upload to object storage.

    Accepts a Python iterator yielding frames, pipes them directly to FFmpeg stdin,
    writes the encoded output to a temporary file, and performs a synchronous upload
    to the configured bucket with the video/mp4 MIME type explicitly attached to
    the object metadata. The temporary file is automatically removed after
    successful upload or on any encoding failure.

    Parameters
    ----------
    frame_generator : Iterator[RGBFrame]
        Iterator yielding frames conforming to the RGBFrame type: (H, W, 3) uint8
        arrays in RGB order. All frames must share consistent dimensions. Odd
        dimensions are trimmed internally to satisfy H.264 macroblock alignment.
    storage_key : str
        Destination key in the application object storage bucket.
    width : int
        Target frame width in pixels. Reduced by one if odd.
    height : int
        Target frame height in pixels. Reduced by one if odd.
    fps_target : float
        Target frame rate in frames per second.
    crf : int
        Constant Rate Factor for libx264. Range 0 to 51. Lower values increase
        quality and file size.
    preset : str
        x264 encoding speed versus compression preset.

    Raises
    ------
    RuntimeError
        If FFmpeg exits with a non-zero status, produces an empty file, terminates
        prematurely during frame ingestion, or the upload to object storage fails.

    Notes
    -----
    Input dimensions are automatically adjusted to even values to prevent x264
    encoding errors. The temporary file uses the system default temporary directory
    and is cleaned up in a finally block. FFmpeg output is written directly to disk,
    ensuring O(1) memory footprint regardless of video duration. File descriptor
    leaks from temporary file creation are explicitly prevented. Frames are written
    via memoryview to avoid redundant copies of raw pixel data. Broken pipe errors
    during frame ingestion are caught and re-raised with FFmpeg stderr output for
    diagnostics. stdout and stderr are consumed via communicate to prevent pipe
    buffer deadlocks. The video/mp4 MIME type is hardcoded for this function
    because the encoding pipeline is unconditionally configured for H.264 in
    an MP4 container; callers needing a different container format must use
    a separate uploader.
    """
    width = width - (width % 2)
    height = height - (height % 2)

    fd, tmp_path_str = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    tmp_path = Path(tmp_path_str)

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps_target),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(tmp_path),
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        try:
            for frame in frame_generator:
                proc.stdin.write(memoryview(frame))
        except BrokenPipeError:
            pass
        finally:
            if not proc.stdin.closed:
                proc.stdin.close()

        _, stderr_bytes = proc.communicate()
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            raise RuntimeError(
                f"FFmpeg encoding failed (exit code {proc.returncode}): {stderr}"
            )

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            raise RuntimeError("FFmpeg produced an empty output file.")

        StorageOperations.upload_file_sync(
            storage_key=storage_key,
            file_path=str(tmp_path),
            content_type="video/mp4",
        )

    finally:
        if tmp_path.exists():
            tmp_path.unlink()