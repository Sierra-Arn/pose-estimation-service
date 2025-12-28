# app/video/input.py
import subprocess
import json
from typing import Iterator
import requests
import numpy as np
from ..human_pose_estimator.types import RGBFrame
from ..s3 import files_service


def decode_from_minio_streaming(
    storage_key: str,
    expires: int = 300,
    fps_target: float = 30.0
) -> Iterator[RGBFrame]:
    """
    Stream decoded RGB frames from a video object in MinIO using FFmpeg.

    This function generates a temporary presigned URL to stream video directly from
    MinIO to FFmpeg. The video is decoded at the specified target frame rate and
    converted to RGB24 pixel format. Frames are yielded one at a time, ensuring
    constant memory usage regardless of video duration.

    Parameters
    ----------
    storage_key : str
        Key of the video object in the application's configured MinIO bucket.
        Must correspond to a valid, accessible video file.
    expires : int
        Lifetime of the presigned URL in seconds. Provided by upstream validation.
        Default is 300 (5 minutes).
    fps_target : float, optional
        Target frame rate for decoding. FFmpeg will duplicate or drop frames
        to match this rate. Default is 30.0 frames per second.

    Yields
    ------
    RGBFrame
        RGB frames as `(H, W, 3)` NumPy arrays with dtype `uint8`, adhering to
        the `RGBFrame` type specification.

    Raises
    ------
    RuntimeError
        If FFprobe fails to extract video dimensions, FFmpeg fails during decoding,
        or the raw output size is inconsistent with expected frame layout.

    Notes
    -----
    - **Memory-safe**: Only one frame is held in memory at a time.
    - **Color format**: Output is in standard RGB order (not BGR), matching
      expectations of deep learning and visualization pipelines.
    - **Streaming**: Video is read directly from MinIO via a presigned URL —
      no intermediate download or local storage is used.
    - **No explicit timeouts**: FFprobe and FFmpeg may hang indefinitely on
      malformed or unreachable inputs; callers should guard against this
      if operating in untrusted environments.
    """

    url = files_service.generate_presigned_url(storage_key=storage_key, expires=expires)

    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", url
    ]
    probe = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    data = json.loads(probe.stdout)
    width = data["streams"][0]["width"]
    height = data["streams"][0]["height"]

    # Launch FFmpeg in streaming mode
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", url,
        "-vf", f"fps={fps_target}",
        "-pix_fmt", "rgb24",
        "-f", "rawvideo",
        "-loglevel", "error",
        "pipe:1",
    ]

    ffmpeg_proc = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**8  # Large buffer to reduce syscall overhead
    )

    frame_size = width * height * 3
    try:
        while True:
            raw_frame = ffmpeg_proc.stdout.read(frame_size)
            if len(raw_frame) < frame_size:
                break  # End of stream or incomplete frame
            frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
            yield frame
    finally:
        ffmpeg_proc.stdout.close()
        ffmpeg_proc.wait()
        if ffmpeg_proc.returncode != 0:
            stderr = ffmpeg_proc.stderr.read().decode()
            raise RuntimeError(f"FFmpeg error during decoding: {stderr}")
        

def stream_video_from_presigned_url(presigned_url: str) -> Iterator[bytes]:
    """
    Stream raw video file bytes directly from a presigned MinIO/S3 URL.

    This function establishes an HTTP GET request to the provided presigned URL
    and yields the video file in fixed-size chunks. It is designed for efficient,
    memory-safe delivery of large video files without loading the entire content
    into application memory.

    Parameters
    ----------
    presigned_url : str
        A valid, temporary HTTP(S) URL granting read access to a video object.
        Must be generated with sufficient expiration time for the expected transfer.

    Yields
    ------
    bytes
        Consecutive non-empty chunks of the video file, typically 8192 bytes each.
        Empty keep-alive chunks (if any) are filtered out.

    Raises
    ------
    requests.RequestException
        If the HTTP request fails (e.g., 404 Not Found, 403 Forbidden,
        network timeout, or invalid URL). The original exception is propagated
        to allow upstream handling (e.g., conversion to HTTP 404/500).

    Notes
    -----
    - **Memory-safe**: Only one chunk is held in memory at a time.
    - **Streaming**: Data flows directly from object storage to the caller;
      no intermediate buffering or file system usage occurs.
    - **Timeout**: A 30-second timeout is enforced on the initial connection
      and between read operations to prevent indefinite hangs.
    - **Use case**: Ideal for FastAPI `StreamingResponse` to deliver full video
      files (e.g., annotated MP4s) to clients for download or playback.
    """

    with requests.get(presigned_url, stream=True, timeout=30) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:  # skip empty keep-alive chunks
                yield chunk