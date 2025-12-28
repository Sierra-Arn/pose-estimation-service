# app/rest/app.py
from fastapi import FastAPI
from .config import rest_config
from .ml_endpoints import ml_router
from .storage_endpoints import storage_router


rest_app = FastAPI(
    title=rest_config.title,
    description=rest_config.description,
    version=rest_config.version
)

rest_app.include_router(storage_router)
rest_app.include_router(ml_router)