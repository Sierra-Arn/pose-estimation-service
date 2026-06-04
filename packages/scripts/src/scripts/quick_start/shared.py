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

# packages/scripts/src/scripts/quick_start/shared.py
import sys
import time
import subprocess
import os
from typing import NamedTuple
from pathlib import Path
import webbrowser
import requests
from dotenv import load_dotenv


class ApiUrls(NamedTuple):
    """
    Container for all API endpoint URLs.
    
    Attributes
    ----------
    base_url : str
        Root URL of the API server.
    health_url : str
        Shallow health check endpoint.
    docs_url : str
        API documentation endpoint.
    ingest_url : str
        Video ingestion endpoint.
    estimation_submit_url : str
        Estimation task submission endpoint.
    visualization_submit_url : str
        Visualization task submission endpoint.
    tasks_base_url : str
        Base endpoint URL for task status polling.
    task_url : str or None
        Task status endpoint with specific task_id, or None if not provided.
    video_url : str or None
        Video details endpoint with specific video_id, or None if not provided.
    """
    base_url: str
    health_url: str
    docs_url: str
    ingest_url: str
    estimation_submit_url: str
    visualization_submit_url: str
    tasks_base_url: str
    task_url: str | None
    video_url: str | None


def run(cmd: list[str], verbose: bool = True) -> None:
    """
    Execute a subprocess command and block until it completes.

    Parameters
    ----------
    cmd : list of str
        Command and arguments passed directly to subprocess.
    verbose : bool, optional
        If True, prints the command and allows standard output to be displayed.
        If False, suppresses stdout and stderr using subprocess.DEVNULL.
        Default is True.
    """
    if verbose:
        print(f"\n>>> {' '.join(cmd)}")
        result = subprocess.run(cmd)
    else:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    if result.returncode != 0:
        sys.exit(result.returncode)


def terminal(cmd: list[str]) -> None:
    """
    Open a new gnome-terminal window and execute a command inside it.

    Parameters
    ----------
    cmd : list of str
        Command and arguments to run inside the new terminal window.
    """
    print(f"\n>>> gnome-terminal: {' '.join(cmd)}")
    subprocess.Popen(["gnome-terminal", "--", "bash", "-c", " ".join(cmd)])


def get_api_urls() -> ApiUrls:
    """
    Load environment variables and construct all base API endpoint URLs.

    Returns
    -------
    ApiUrls
        A NamedTuple containing all base API URLs. task_url and video_url
        will be None and should be populated using add_video_url or add_task_url.
    """
    load_dotenv(Path.cwd() / ".env")

    host = os.getenv("SERVER_HOST")
    port = os.getenv("SERVER_PORT")
    docs = os.getenv("SERVER_DOCS_URL")

    base_url = f"http://{host}:{port}"
    
    return ApiUrls(
        base_url=base_url,
        health_url=f"{base_url}/health/shallow/",
        docs_url=f"{base_url}{docs}",
        ingest_url=f"{base_url}/videos/ingest/",
        estimation_submit_url=f"{base_url}/estimations/submit/",
        visualization_submit_url=f"{base_url}/visualizations/submit/",
        tasks_base_url=f"{base_url}/tasks/",
        task_url=None,
        video_url=None,
    )


def add_video_url(urls: ApiUrls, video_id: str) -> ApiUrls:
    """
    Create a new ApiUrls instance with the video_url populated.

    Parameters
    ----------
    urls : ApiUrls
        Base ApiUrls instance.
    video_id : str
        Specific video identifier to form the video details URL.

    Returns
    -------
    ApiUrls
        A new ApiUrls instance with video_url set to the specific video endpoint.
    """
    video_url = f"{urls.base_url}/videos/{video_id}/"
    return urls._replace(video_url=video_url)


def add_task_url(urls: ApiUrls, task_id: str) -> ApiUrls:
    """
    Create a new ApiUrls instance with the task_url populated.

    Parameters
    ----------
    urls : ApiUrls
        Base ApiUrls instance.
    task_id : str
        Specific task identifier to form the task status URL.

    Returns
    -------
    ApiUrls
        A new ApiUrls instance with task_url set to the specific task endpoint.
    """
    task_url = f"{urls.base_url}/tasks/{task_id}/"
    return urls._replace(task_url=task_url)


def start_infrastructure(deploy: bool = False, verbose: bool = True) -> None:
    """
    Generate environment configurations and start Docker containers.

    Parameters
    ----------
    deploy : bool, optional
        If True, generates deploy-specific environment and starts production containers.
        If False, generates local development environment and starts local containers.
        Default is False.
    verbose : bool, optional
        If True, prints informational messages and allows command outputs.
        If False, suppresses informational messages and command outputs.
        Default is True.
    """
    if verbose:
        print("[info] initializing environment and infrastructure...")
    
    if deploy:
        run(["just", "gen-env", "deploy"], verbose=verbose)
        run(["just", "gen-acl"], verbose=verbose)
        run(["just", "gen-sql"], verbose=verbose)
        run(["just", "gen-minio"], verbose=verbose)
        run(["just", "docker-deploy-up"], verbose=verbose)
    else:
        run(["just", "gen-env"], verbose=verbose)
        run(["just", "gen-acl"], verbose=verbose)
        run(["just", "gen-sql"], verbose=verbose)
        run(["just", "gen-minio"], verbose=verbose)
        run(["just", "docker-local-up"], verbose=verbose)
        
        if verbose:
            print("[info] waiting for infrastructure to start")
        time.sleep(10)
        run(["just", "db-migrate"], verbose=verbose)


def wait_for_server(urls: ApiUrls, retries: int = 20, interval: int = 10) -> bool:
    """
    Poll the server health endpoint until it returns HTTP 200 or the retry limit is reached.

    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing the health_url endpoint to poll.
    retries : int, optional
        Maximum number of attempts before giving up. Default is 20.
    interval : int, optional
        Number of seconds to wait between attempts. Default is 10.

    Returns
    -------
    bool
        True if the server responded with HTTP 200 within the retry limit.
        False if all attempts were exhausted without a successful response.
    """
    print(f"\n[info] waiting for server at {urls.health_url}")
    for _ in range(retries):
        try:
            response = requests.get(urls.health_url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    return False


def check_health_and_open_docs(urls: ApiUrls) -> bool:
    """
    Check server health and automatically open documentation in the browser.

    Parameters
    ----------
    urls : ApiUrls
        NamedTuple containing health_url and docs_url endpoints.

    Returns
    -------
    bool
        True if the server is healthy and the browser was opened.
        False if the server did not respond in time.
    """
    if wait_for_server(urls):
        print(f"\n[info] server is healthy, opening {urls.docs_url}")
        webbrowser.open(urls.docs_url)
        return True
    else:
        print(f"[warn] server did not respond in time, open manually: {urls.docs_url}")
        return False