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

# packages/scripts/src/scripts/utils/init_env.py
"""
Initialize environment configuration from a template.

This script reads a specified environment template, generates cryptographically
secure passwords for credential fields, and writes the result to a .env file
in the project root.

Usage
-----
To initialize the local environment (default):
    pixi run python -m scripts.utils.init_env

To initialize the deploy environment:
    pixi run python -m scripts.utils.init_env --template deploy
"""
import argparse
import secrets
import string
import sys
from pathlib import Path

TEMPLATE_MAP = {
    "local": ".env.local.example",
    "deploy": ".env.deploy.example",
}


def _generate_secure_password(length: int = 32) -> str:
    """
    Generate a cryptographically secure random password.

    Parameters
    ----------
    length : int, optional
        Desired password length. Default is 32.

    Returns
    -------
    str
        Random password composed of ASCII letters and digits.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def init_env(template_choice: str, password_length: int = 32) -> Path:
    """
    Initialize environment configuration from template.

    Copies the specified example file, generates cryptographically secure
    passwords for credential fields, and writes the result to .env in the
    project root.

    Parameters
    ----------
    template_choice : str
        Environment type to initialize. Must be 'local' or 'deploy'.
    password_length : int, optional
        Length of generated secrets. Default is 32.

    Returns
    -------
    Path
        Absolute path to the created .env file.

    Raises
    ------
    FileNotFoundError
        If the specified template file does not exist in the config directory.
    OSError
        If the template cannot be read or the .env file cannot be written due
        to permissions or path issues.

    Notes
    -----
    If the .env file already exists at the project root, the function returns
    its path immediately without reading the template or generating new credentials.
    """
    output_path = Path.cwd() / ".env"
    if output_path.exists():
        return output_path.resolve()

    template_path = Path.cwd() / "config" / TEMPLATE_MAP[template_choice]
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    credential_keywords = {"PASSWORD"}
    placeholder_values = {"changeme"}

    lines = []
    for line in template_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            lines.append(line)
            continue

        key, _, raw_value = stripped.partition("=")
        value = raw_value.strip().strip("\"'")
        key_upper = key.strip().upper()

        is_credential = any(kw in key_upper for kw in credential_keywords)
        is_placeholder = not value or value.lower() in placeholder_values

        if is_credential and is_placeholder:
            lines.append(f"{key}={_generate_secure_password(password_length)}")
        else:
            lines.append(line)

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize .env file from local or deploy template."
    )
    parser.add_argument(
        "--template",
        choices=["local", "deploy"],
        default="local",
        help="Environment template to use. Default is 'local'.",
    )
    args = parser.parse_args()

    try:
        path = init_env(template_choice=args.template)
        print(f"Environment initialized successfully: {path}")
        sys.exit(0)
    except (FileExistsError, FileNotFoundError) as exc:
        print(f"Setup aborted: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)