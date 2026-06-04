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

# packages/shared/src/task_queue/infrastructure/frame_extractor.py
import subprocess
import numpy as np
from typing import Iterator
from ensam3d_inference.preprocessor.detector.types import RGBFrame
from minio_lib import StorageOperations


def decode_video_stream_batches(
    storage_key: str,
    target_width: int,
    target_height: int,
    target_fps: float,
    batch_size: int,
    skip_start_seconds: float,
    duration_seconds: float | None,
    expires: int = 3600,
) -> Iterator[list[RGBFrame]]:
    """
    Decode and preprocess video frames from object storage using FFmpeg.

    Fetches a time-limited presigned URL, then streams decoded, rescaled,
    and fps-adjusted frames in batches as lists of RGBFrame objects.
    All filtering is performed natively by FFmpeg in a single pass.
    The returned lists are structurally compatible with PreprocessorInput.

    Parameters
    ----------
    storage_key : str
        Object storage key identifying the source video file.
    target_width : int
        Output frame width in pixels. Automatically rounded down to
        the nearest even value for H.264 compatibility.
    target_height : int
        Output frame height in pixels. Automatically rounded down to
        the nearest even value for H.264 compatibility.
    target_fps : float
        Target frame rate for output frames.
    batch_size : int
        Number of frames to accumulate and yield per iteration.
    skip_start_seconds : float, optional
        Temporal offset in seconds to skip from video start before
        decoding begins.
    duration_seconds : float or None
        Maximum duration of frames to yield in seconds. If None,
        decoding continues to the end of the stream.
    expires : int, optional
        Lifetime of the presigned URL in seconds. Default is 3600.

    Yields
    ------
    list of RGBFrame
        Batch of frames as a list of (H, W, 3) uint8 NumPy arrays.
        Each element is a view into a shared read buffer for zero-copy
        efficiency. The final batch may contain fewer frames if the
        video ends before the requested batch size.

    Raises
    ------
    RuntimeError
        If FFmpeg fails to start, encounters a decoding error, or
        the presigned URL is inaccessible. Error message includes
        FFmpeg stderr output for downstream diagnostics.

    WARNING
    -------
    Each frame in the yielded list is a view into a local bytes
    buffer allocated per loop iteration, not an independent copy. This is
    intentional to minimize memory consumption: no extra allocation per
    frame regardless of resolution or batch size. The current call site
    in the visualize task processes every frame synchronously before the
    generator advances, so the underlying buffer is never overwritten while
    views are still live. If consumption ever becomes asynchronous or the
    frames are stored across iterations, callers must call frame.copy() on
    each element to take ownership of the data.
    """
    target_width = target_width - (target_width % 2)
    target_height = target_height - (target_height % 2)

    url = StorageOperations.generate_presigned_get_url(
        storage_key=storage_key,
        expires=expires,
    )

    vf_filters = [
        f"fps={target_fps}:round=down",
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:flags=lanczos",
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2",
    ]

    cmd = [
        "ffmpeg",
        "-v", "error",
        "-ss", str(skip_start_seconds),
        "-i", url,
        "-vf", ",".join(vf_filters),
        "-pix_fmt", "rgb24",
        "-f", "rawvideo",
        "-an",
        "-sn",
        "-dn",
    ]

    if duration_seconds is not None:
        cmd.extend(["-t", str(duration_seconds)])

    cmd.append("pipe:1")

    frame_size = target_width * target_height * 3
    batch_byte_size = batch_size * frame_size

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        while True:
            raw_batch = proc.stdout.read(batch_byte_size)
            if not raw_batch:
                break

            n_frames = len(raw_batch) // frame_size
            if n_frames == 0:
                break

            batch_bytes = raw_batch[: n_frames * frame_size]
            batch_array = np.frombuffer(batch_bytes, dtype=np.uint8).reshape(
                n_frames, target_height, target_width, 3
            )

            yield list(batch_array)

    finally:
        proc.stdout.close()
        _, stderr_bytes = proc.communicate()

        if proc.returncode != 0:
            stderr = stderr_bytes.decode(errors="ignore").strip()
            raise RuntimeError(
                f"FFmpeg decoding failed (code {proc.returncode}): {stderr[:500]}"
            )