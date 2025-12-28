# app/rest/main.py
import uvicorn
from .config import rest_config
from .app import rest_app


if __name__ == "__main__":
    uvicorn.run(
        app=rest_app,
        host=rest_config.host,
        port=rest_config.port,
        log_level=rest_config.log_level.lower(),
    )