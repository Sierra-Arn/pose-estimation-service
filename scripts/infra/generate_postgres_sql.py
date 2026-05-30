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

# scripts/infra/generate_postgres_sql.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def generate_sql_script() -> Path:
    """
    Generate PostgreSQL initialization SQL script from environment variables.

    Unconditionally writes the SQL file to docker/postgres/init/01-create-user.sql.
    Creates parent directories if they do not exist.

    Returns
    -------
    Path
        Absolute path to the generated SQL file.

    Raises
    ------
    RuntimeError
        If any required environment variable is missing.
    OSError
        If the file cannot be created or written due to permissions or path issues.
    """
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "docker" / "postgres" / "init" / "01-create-user.sql"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

    env_vars = {
        "POSTGRES_USER_NAME": os.getenv("POSTGRES_USER_NAME"),
        "POSTGRES_USER_PASSWORD": os.getenv("POSTGRES_USER_PASSWORD"),
        "POSTGRES_USER_DB_NAME": os.getenv("POSTGRES_USER_DB_NAME"),
    }

    missing = [name for name, value in env_vars.items() if value is None]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    sql_content = (
        f"CREATE USER \"{env_vars['POSTGRES_USER_NAME']}\" WITH PASSWORD '{env_vars['POSTGRES_USER_PASSWORD']}';\n"
        f"CREATE DATABASE \"{env_vars['POSTGRES_USER_DB_NAME']}\";\n"
        f"\\c {env_vars['POSTGRES_USER_DB_NAME']}\n"
        f"REVOKE CREATE ON SCHEMA public FROM PUBLIC;\n"
        f"GRANT CONNECT ON DATABASE \"{env_vars['POSTGRES_USER_DB_NAME']}\" TO \"{env_vars['POSTGRES_USER_NAME']}\";\n"
        f"GRANT USAGE ON SCHEMA public TO \"{env_vars['POSTGRES_USER_NAME']}\";\n"
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public\n"
        f"GRANT SELECT, INSERT, DELETE ON TABLES TO \"{env_vars['POSTGRES_USER_NAME']}\";\n"
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public\n"
        f"GRANT USAGE, SELECT ON SEQUENCES TO \"{env_vars['POSTGRES_USER_NAME']}\";\n"
    )

    output_path.write_text(sql_content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    try:
        path = generate_sql_script()
        print(f"SQL script successfully generated: {path}")
        sys.exit(0)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"File system error: {exc}", file=sys.stderr)
        sys.exit(1)