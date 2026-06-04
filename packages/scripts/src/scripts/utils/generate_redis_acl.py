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

# packages/scripts/src/scripts/utils/generate_redis_acl.py
"""
Generate Redis ACL configuration file from environment variables.

This script reads environment variables to generate a Redis ACL file.
The file defines users and their permissions upon container startup.

Usage
-----
To generate the ACL file in the default directory:
    pixi run python -m scripts.utils.generate_acl_file

To specify a custom output directory:
    pixi run python -m scripts.utils.generate_acl_file --output-dir /custom/path
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def generate_acl_file(output_dir: Path) -> Path:
    """
    Generate Redis ACL configuration file from environment variables.

    Unconditionally writes the ACL file to the specified directory.
    Creates parent directories if they do not exist.

    Parameters
    ----------
    output_dir : Path
        The directory where 01-create-users.acl will be saved.

    Returns
    -------
    Path
        Absolute path to the generated ACL file.

    Raises
    ------
    RuntimeError
        If any required environment variable is missing.
    OSError
        If the file cannot be created or written due to permissions or path issues.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "01-create-users.acl"

    load_dotenv(Path.cwd() / ".env")

    env_vars = {
        "REDIS_ADMIN_NAME": os.getenv("REDIS_ADMIN_NAME"),
        "REDIS_ADMIN_PASSWORD": os.getenv("REDIS_ADMIN_PASSWORD"),
        "REDIS_USER_NAME": os.getenv("REDIS_USER_NAME"),
        "REDIS_USER_PASSWORD": os.getenv("REDIS_USER_PASSWORD"),
    }

    missing = [name for name, value in env_vars.items() if value is None]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    acl_content = (
        f"user {env_vars['REDIS_ADMIN_NAME']} on >{env_vars['REDIS_ADMIN_PASSWORD']} ~* &* +@all\n"
        f"user {env_vars['REDIS_USER_NAME']} on >{env_vars['REDIS_USER_PASSWORD']} ~* &* +@all -@dangerous -@admin\n"
        "user default off nopass\n"
    )

    output_path.write_text(acl_content, encoding="utf-8")
    return output_path.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Redis ACL configuration file from environment variables."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd() / "docker" / "redis" / "init",
        help="Directory to save the generated ACL file. Defaults to ./docker/redis/init.",
    )
    args = parser.parse_args()

    try:
        path = generate_acl_file(args.output_dir)
        print(f"ACL file successfully generated: {path}")
        sys.exit(0)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"File system error: {exc}", file=sys.stderr)
        sys.exit(1)