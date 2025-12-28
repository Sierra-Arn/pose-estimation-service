# app/rest/config.py
from typing import ClassVar, Literal
from pydantic import Field
from ..shared import BaseConfig


class RESTConfig(BaseConfig):
    """
    Configuration for the FastAPI server.

    Attributes
    ----------
    title : str
        Human-readable title of the API. Displayed in the generated
        OpenAPI schema and `/docs` UI. Default is `"Human Pose Pipeline API"`.

    description : str
        Detailed description of the API's purpose. Used in documentation UI.
        Default is `"Analyzes running form from video and returns recommendations for improvement."`.

    version : str
        Semantic version string of the server API. Default is `"0.1.0"`.

    host : str
        Host interface the server binds to. Default is `"127.0.0.1"`.

    port : int
        TCP port the server listens on. Must be in the range 1-65535.
        Default is `8000`.

    log_level : Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        Logging severity level for the application. Default is `"INFO"`.

    storage_router_prefix : str
        URL path prefix applied to storage API routes.
        Default is `"/storage/v1"`.

    ml_router_prefix : str
        URL path prefix applied to ML API routes.
        Default is `"/ml/v1"`.

    input_video_name : str
        Filename for the uploaded input video.
        Default is `"input_video"`.

    output_video_name : str
        Filename for the annotated output video produced by the pipeline.
        Default is `"output_video"`.

    estimation_results_name : str
        Filename for the estimation results in pickle format.
        Default is `"estimations"`.

    running_analysis_name : str
        Filename for the running analysis in pickle format.
        Default is `"analysis"`.

    Notes
    -----
    This class inherits from `app.shared.base_config.BaseConfig`.
    For details on configuration loading behavior, see its documentation.
    """

    env_prefix: ClassVar[str] = "REST_"

    title: str = "Human Pose Pipeline API"
    description: str = "Analyzes running form from video and returns recommendations for improvement."
    version: str = "0.1.0"

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    storage_router_prefix: str = "/storage/v1"
    ml_router_prefix: str = "/ml/v1"

    input_video_name: str = "input_video"
    output_video_name: str = "output_video"
    estimation_results_name: str = "estimation_results"
    running_analysis_name: str = "running_analysis"


# Initialize REST API configuration singleton
# Since REST API settings are static for the application's lifetime
# and any changes require a restart to take effect,
# it is safe and efficient to instantiate this configuration once at module level
# and reuse it throughout the application as a singleton.
rest_config = RESTConfig()