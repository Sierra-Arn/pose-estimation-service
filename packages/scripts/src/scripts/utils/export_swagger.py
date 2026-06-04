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

# packages/scripts/src/scripts/utils/export_swagger.py
"""
Export OpenAPI specification to a YAML file.

This script instantiates the FastAPI application, retrieves the auto-generated
OpenAPI schema, and serializes it to a specified YAML file. The output uses
block-style formatting and preserves unicode characters for readability.

Usage
-----
To export the schema to the default location in the current directory:
    pixi run -e server python -m scripts.utils.export_swagger

To specify a custom output path:
    pixi run -e server python -m scripts.utils.export_swagger -o /path/to/custom/openapi.yaml
    pixi run -e server python -m scripts.utils.export_swagger --output /path/to/custom/openapi.yaml
"""
import sys
import argparse
from pathlib import Path
import yaml


def export_swagger(output_path: Path) -> Path:
    """
    Export the application OpenAPI specification to a YAML file.

    Instantiates the FastAPI application, retrieves the auto-generated
    OpenAPI schema, and serializes it to the specified file path.
    The output uses block-style formatting and preserves unicode characters
    for readability.

    Parameters
    ----------
    output_path : Path
        The absolute or relative path where the openapi.yaml file will be saved.

    Returns
    -------
    Path
        Absolute path to the generated openapi.yaml file.

    Raises
    ------
    OSError
        If the file cannot be created or written due to permissions or path issues.
    """
    from server.app import create_app
    schema = create_app().openapi()

    with output_path.open("w", encoding="utf-8") as f:
        yaml.dump(schema, f, allow_unicode=True, default_flow_style=False)

    return output_path.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export the FastAPI OpenAPI specification to a YAML file."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.cwd() / "openapi.yaml",
        help="Path to save the openapi.yaml file. Defaults to the current working directory."
    )
    args = parser.parse_args()

    try:
        output_path = export_swagger(args.output)
        print(f"OpenAPI specification successfully exported: {output_path}")
        sys.exit(0)
    except OSError as exc:
        print(f"File system error: {exc}", file=sys.stderr)
        sys.exit(1)