# app/rest/ml_endpoints/__init__.py
from .estimation_request import request_estimation
from .analysis_request import request_analysis
from .video_request import request_video

from .router import ml_router