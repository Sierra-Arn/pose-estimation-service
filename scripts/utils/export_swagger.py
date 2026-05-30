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

# scripts/utils/export_swagger.py
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import yaml
from app.server.app import create_app


def export_swagger() -> Path:
    """
    Export the application's OpenAPI specification to a YAML file.

    Instantiates the FastAPI application, retrieves the auto-generated
    OpenAPI schema, and serializes it to the project root as openapi.yaml.
    The output uses block-style formatting and preserves unicode characters
    for readability.

    Returns
    -------
    Path
        Absolute path to the generated openapi.yaml file.

    Raises
    ------
    OSError
        If the file cannot be created or written due to permissions or path issues.
    """
    output_path = project_root / "openapi.yaml"
    schema = create_app().openapi()

    with output_path.open("w", encoding="utf-8") as f:
        yaml.dump(schema, f, allow_unicode=True, default_flow_style=False)

    return output_path


if __name__ == "__main__":
    try:
        output_path = export_swagger()
        print(f"OpenAPI specification successfully exported: {output_path}")
        sys.exit(0)
    except OSError as exc:
        print(f"File system error: {exc}", file=sys.stderr)
        sys.exit(1)
