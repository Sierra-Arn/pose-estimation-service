# app/rest/storage_endpoints/router.py
from fastapi import APIRouter
from ..config import rest_config

storage_router = APIRouter(
    prefix=rest_config.storage_router_prefix,
    tags=[rest_config.storage_router_prefix]
)