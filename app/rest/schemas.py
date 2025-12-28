# app/rest/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from ..running_analysis import AnatomicalSide


class PoseEstimationRequest(BaseModel):
    """
    Request schema for initiating 2D human pose estimation on an uploaded video.
    """
    
    video_id: str = Field(
        ...,
        description="UUID4 string identifying the uploaded video. Must correspond to an existing input video in storage."
    )
    
    fps: float = Field(
        30.0,
        ge=1,
        le=120,
        description=
            "Target frame rate (in frames per second) for video decoding and pose estimation. "
            "FFmpeg will upsample or downsample the input stream to match this rate. "
            "Lower values reduce processing time and output size but may miss fast motion details. "
            "Warning: Some video codecs may produce corrupted or green frames when `video_fps` is set below 5.0."
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "video_id": "a1b2c3d4-5678-90ef-1234-567890abcdef",
                    "fps": 30.0
                }
            ]
        }
    )


class VideoRenderRequest(PoseEstimationRequest):
    """
    Request schema for rendering an annotated video with pose overlays.
    """
    
    crf: int = Field(
        22,
        description=(
            "Constant Rate Factor for H.264 video encoding (range 0-51). "
            "Lower values yield higher quality and larger file sizes. "
            "Typical range: 18 (visually lossless) to 28 (web streaming)."
        )
    )
    
    show_bbox: bool = Field(
        True,
        description="Whether to draw the person detection bounding box (if available)."
    )
    
    show_keypoints: bool = Field(
        True,
        description="Whether to render detected keypoints as colored circles."
    )
    
    show_confidence: bool = Field(
        False,
        description="Whether to overlay keypoint confidence scores as text labels."
    )
    
    show_skeleton: bool = Field(
        True,
        description="Whether to draw skeleton connections between anatomically linked keypoints."
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "video_id": "a1b2c3d4-5678-90ef-1234-567890abcdef",
                    "fps": 30.0,
                    "crf": 22,
                    "show_bbox": True,
                    "show_keypoints": True,
                    "show_confidence": False,
                    "show_skeleton": True
                }
            ]
        }
    )


class RunningAnalysisRequest(BaseModel):
    """
    Request schema for running analysis of pose estimation results.
    """
    
    video_id: str = Field(
        ...,
        description="UUID4 string identifying the video. Must have existing pose estimation results."
    )
    
    side: AnatomicalSide = Field(
        "right",
        description="Anatomical side of the body to analyze ('left' or 'right')."
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "video_id": "a1b2c3d4-5678-90ef-1234-567890abcdef",
                    "side": "right"
                }
            ]
        }
    )