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

# scripts/quick_start/local.py
import os
import sys
import time
import webbrowser
import subprocess
import urllib.request
from pathlib import Path
from dotenv import load_dotenv


def run(cmd: list[str], allow_failure: bool = False) -> None:
    """
    Execute a subprocess command and block until it completes.

    Parameters
    ----------
    cmd : list of str
        Command and arguments passed directly to subprocess.
    allow_failure : bool, optional
        If True, a non-zero exit code prints a warning and continues.
        If False, a non-zero exit code prints an error and exits the process.
        Default is False.
    """
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        if allow_failure:
            print(f"[warn] command exited with code {result.returncode}, continuing")
        else:
            print(f"[error] command failed with code {result.returncode}, aborting")
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


def wait_for_server(url: str, retries: int = 20, interval: int = 10) -> bool:
    """
    Poll a URL until it returns HTTP 200 or the retry limit is reached.

    Parameters
    ----------
    url : str
        Full URL to poll. Expected to be a shallow health check endpoint.
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
    print(f"\n[info] waiting for server at {url}")
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(interval)
    return False


if __name__ == "__main__":

    run(["just", "gen-env"])
    run(["just", "gen-acl"])
    run(["just", "gen-sql"])
    run(["just", "gen-minio"])
    run(["just", "docker-local-up"])

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

    host = os.getenv("SERVER_HOST")
    port = os.getenv("SERVER_PORT")
    docs = os.getenv("SERVER_DOCS_URL")

    health_url = f"http://{host}:{port}/health/shallow/"
    docs_url = f"http://{host}:{port}{docs}"

    print("\n[info] waiting for infrastructure to start")
    time.sleep(10)
    run(["just", "db-revision-auto"], allow_failure=True)
    run(["just", "db-migrate"])

    terminal(["just", "server"])
    terminal(["just", "worker-default"])
    terminal(["just", "worker-inference"])

    if wait_for_server(health_url):
        print(f"\n[info] server is healthy, opening {docs_url}")
        webbrowser.open(docs_url)
    else:
        print(f"[warn] server did not respond in time, open manually: {docs_url}")