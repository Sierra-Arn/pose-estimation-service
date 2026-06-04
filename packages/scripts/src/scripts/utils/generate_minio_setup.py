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

# packages/scripts/src/scripts/utils/generate_minio_setup.py
"""
Generate MinIO initialization artifacts from environment variables.

This script reads environment variables to generate a MinIO policy file
and a setup shell script. These artifacts are used to initialize MinIO
buckets, users, and policies upon container startup.

Usage
-----
To generate the artifacts in the default directory:
    pixi run python -m scripts.utils.generate_minio_setup

To specify a custom output directory:
    pixi run python -m scripts.utils.generate_minio_setup --output-dir /custom/path
"""
import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from dotenv import load_dotenv


def generate_minio_setup(output_dir: Path) -> tuple[Path, Path]:
    """
    Generate MinIO initialization artifacts from environment variables.

    Unconditionally writes policy.json and setup.sh to the specified directory.
    Creates parent directories if they do not exist.

    Parameters
    ----------
    output_dir : Path
        The directory where policy.json and setup.sh will be saved.

    Returns
    -------
    tuple[Path, Path]
        Absolute paths to the generated policy.json and setup.sh files.

    Raises
    ------
    RuntimeError
        If any required environment variable is missing.
    OSError
        If files cannot be created or written due to permissions or path issues.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    policy_path = output_dir / "policy.json"
    setup_path = output_dir / "setup.sh"

    load_dotenv(Path.cwd() / ".env")

    env_vars = {
        "MINIO_ROOT_NAME": os.getenv("MINIO_ROOT_NAME"),
        "MINIO_ROOT_PASSWORD": os.getenv("MINIO_ROOT_PASSWORD"),
        "MINIO_USER_NAME": os.getenv("MINIO_USER_NAME"),
        "MINIO_USER_PASSWORD": os.getenv("MINIO_USER_PASSWORD"),
        "MINIO_USER_BUCKET_NAME": os.getenv("MINIO_USER_BUCKET_NAME"),
        "MINIO_USER_POLICY_NAME": os.getenv("MINIO_USER_POLICY_NAME"),
        "INIT_MINIO_HOST": os.getenv("INIT_MINIO_HOST"),
        "MINIO_INTERNAL_PORT": os.getenv("MINIO_INTERNAL_PORT"),
    }

    missing = [name for name, value in env_vars.items() if value is None]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    bucket_name = env_vars["MINIO_USER_BUCKET_NAME"]
    bucket_arn = f"arn:aws:s3:::{bucket_name}"
    objects_arn = f"arn:aws:s3:::{bucket_name}/*"

    policy_content = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BucketMeta",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:ListBucketMultipartUploads",
                ],
                "Resource": bucket_arn,
            },
            {
                "Sid": "ObjectCrud",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                    "s3:ListMultipartUploadParts",
                ],
                "Resource": objects_arn,
            },
        ],
    }

    endpoint = f"http://{env_vars['INIT_MINIO_HOST']}:{env_vars['MINIO_INTERNAL_PORT']}"
    policy_name = env_vars["MINIO_USER_POLICY_NAME"]

    setup_content = (
        "#!/bin/sh\n"
        "set -e\n"
        "\n"
        f"mc alias set local {shlex.quote(endpoint)} "
        f"{shlex.quote(env_vars['MINIO_ROOT_NAME'])} "
        f"{shlex.quote(env_vars['MINIO_ROOT_PASSWORD'])}\n"
        "\n"
        f"mc admin user add local {shlex.quote(env_vars['MINIO_USER_NAME'])} "
        f"{shlex.quote(env_vars['MINIO_USER_PASSWORD'])} || true\n"
        f"mc admin policy create local {shlex.quote(policy_name)} /init/policy.json || true\n"
        f"mc admin policy attach local {shlex.quote(policy_name)} "
        f"--user {shlex.quote(env_vars['MINIO_USER_NAME'])} || true\n"
        f"mc mb local/{bucket_name} || true\n"
    )

    policy_path.write_text(json.dumps(policy_content, indent=2) + "\n", encoding="utf-8")
    setup_path.write_text(setup_content, encoding="utf-8")
    setup_path.chmod(0o755)

    return policy_path.resolve(), setup_path.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate MinIO initialization artifacts from environment variables."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd() / "docker" / "minio" / "init",
        help="Directory to save the generated files. Defaults to ./docker/minio/init.",
    )
    args = parser.parse_args()

    try:
        policy_path, setup_path = generate_minio_setup(args.output_dir)
        print(f"Policy file successfully generated: {policy_path}")
        print(f"Setup script successfully generated: {setup_path}")
        sys.exit(0)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"File system error: {exc}", file=sys.stderr)
        sys.exit(1)