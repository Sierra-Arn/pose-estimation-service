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

# scripts/infra/generate_minio_setup.py
import json
import os
import shlex
import sys
from pathlib import Path
from dotenv import load_dotenv


def generate_minio_setup() -> tuple[Path, Path]:
    """
    Generate MinIO initialization artifacts from environment variables.

    Unconditionally writes policy.json and setup.sh to docker/minio/init/.
    Creates parent directories if they do not exist.

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
    project_root = Path(__file__).resolve().parents[2]
    init_dir = project_root / "docker" / "minio" / "init"
    policy_path = init_dir / "policy.json"
    setup_path = init_dir / "setup.sh"
    init_dir.mkdir(parents=True, exist_ok=True)

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

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

    return policy_path, setup_path


if __name__ == "__main__":
    try:
        policy_path, setup_path = generate_minio_setup()
        print(f"Policy file successfully generated: {policy_path}")
        print(f"Setup script successfully generated: {setup_path}")
        sys.exit(0)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"File system error: {exc}", file=sys.stderr)
        sys.exit(1)
