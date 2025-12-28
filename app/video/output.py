# app/video/output.py
import subprocess
from io import BytesIO
from typing import Iterator
from ..human_pose_estimator.types import RGBFrame
from ..s3 import files_service


def encode_and_upload_to_minio_streaming(
    frame_generator: Iterator[RGBFrame],
    storage_key: str,
    width: int,
    height: int,
    fps_target: float = 30.0,
    crf: int = 22,
) -> None:
    """
    Encode a stream of RGB frames into an MP4 video and upload directly to MinIO.

    This function consumes frames from an iterator and pipes them directly into
    FFmpeg for H.264/MP4 encoding. The resulting video is uploaded to MinIO without
    intermediate temporary files or full in-memory buffering, ensuring constant
    memory footprint even for long videos.

    Parameters
    ----------
    frame_generator : Iterator[RGBFrame]
        Iterator yielding frames conforming to the `RGBFrame` type: `(H, W, 3)` uint8 arrays
        in RGB order. All frames must share consistent dimensions. Non-even dimensions
        are trimmed internally to satisfy H.264 constraints.
    storage_key : str
        Destination key in the application's MinIO bucket.
    width : int
        Frame width (in pixels). Odd values are reduced by 1 to satisfy H.264.
    height : int
        Frame height (in pixels). Odd values are reduced by 1 to satisfy H.264.
    fps_target : float, optional
        Target frame rate in frames per second. Default is 30.0.
    crf : int, optional
        Constant Rate Factor for libx264 (range 0-51). Lower values yield higher
        quality and larger files. Default is 22.

    Raises
    ------
    RuntimeError
        If FFmpeg fails during encoding or the upload to MinIO fails.

    Notes
    -----
    - **H.264 compliance**: Input dimensions are automatically adjusted to even values.
    - **Streaming I/O**: FFmpeg reads from stdin and writes to stdout; no full video
      is buffered in application memory.
    - **Fragmented MP4**: Output uses `frag_keyframe+empty_moov` for immediate streaming
      playback (e.g., in browsers or mobile players).
    - **Error resilience**: Broken pipe errors (e.g., from empty input) are caught and
      re-raised with descriptive messages.
    """
    
    # Adjust to even dimensions for H.264 compatibility
    if width % 2 != 0:
        width -= 1
    if height % 2 != 0:
        height -= 1

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps_target),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-r", str(fps_target),
        "-movflags", "frag_keyframe+empty_moov",
        "-f", "mp4",
        "pipe:1"
    ]

    ffmpeg_proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        for frame in frame_generator:
            # Trim to even-aligned dimensions if needed
            if frame.shape[0] != height or frame.shape[1] != width:
                frame = frame[:height, :width]
            ffmpeg_proc.stdin.write(frame.tobytes())

        # Close stdin and collect output
        stdout, stderr = ffmpeg_proc.communicate()

        if ffmpeg_proc.returncode != 0:
            raise RuntimeError(f"FFmpeg encoding failed: {stderr.decode()}")

        files_service.upload_fileobj(
            storage_key=storage_key,
            fileobj=BytesIO(stdout)
        )

    except BrokenPipeError:
        # FFmpeg exited early (e.g., no input frames)
        stderr = ffmpeg_proc.stderr.read()
        ffmpeg_proc.wait()
        raise RuntimeError(f"FFmpeg crashed during encoding: {stderr.decode()}")