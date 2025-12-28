# app/rest/ml_endpoints/router.py
from fastapi import APIRouter
from ..config import rest_config

ml_router = APIRouter(
    prefix=rest_config.ml_router_prefix,
    tags=[rest_config.ml_router_prefix]
)