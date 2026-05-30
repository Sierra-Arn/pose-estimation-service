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

# migrations/env.py
import os
from pathlib import Path
import sys
from logging.config import fileConfig
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

load_dotenv()

# Add the parent directory to sys.path to allow imports from the project
# This is crucial for Alembic to find the application modules
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Import models and configuration
# These imports are essential for Alembic to detect the models and generate migrations
from app.shared.postgres import Base, Video, Estimation, Visualization

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers as defined in alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

env_vars = {
    "SUPERUSER_NAME": os.environ["POSTGRES_SUPERUSER_NAME"],
    "SUPERUSER_PASSWORD": os.environ["POSTGRES_SUPERUSER_PASSWORD"],
    "USER_DB_NAME": os.environ["POSTGRES_USER_DB_NAME"],
    "HOST": os.environ["POSTGRES_HOST"],
    "PORT": os.environ["POSTGRES_PORT"],
}

db_url = (
    f"postgresql+psycopg2://{env_vars['SUPERUSER_NAME']}:{quote_plus(env_vars['SUPERUSER_PASSWORD'])}"
    f"@{env_vars['HOST']}:{env_vars['PORT']}/{env_vars['USER_DB_NAME']}"
)

# Get application settings and set the database URL in the Alembic configuration
# This is critical - it overrides any URL in alembic.ini with application's actual DB URL from config
config.set_main_option("sqlalchemy.url", db_url)

# Add the model's MetaData object here for 'autogenerate' support
# This is vital - it tells Alembic which tables to track for migrations
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This mode doesn't require a database connection. It generates SQL scripts
    that would need to be run manually. Useful for generating migration scripts
    to be run in production environments where direct DB access isn't available.
    """

    # Get the database URL from config
    url = config.get_main_option("sqlalchemy.url")
    
    # Configure the migration context
    context.configure(
        url=url,
        target_metadata=target_metadata,        # Our models' metadata
        literal_binds=True,                     # Use literal values in generated SQL
        dialect_opts={"paramstyle": "named"}    # Use named parameters
    )
    
    # Run the migrations within a transaction
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    This is the normal mode where Alembic connects directly to the database
    and applies migrations.
    
    In this scenario we need to create an Engine and associate a connection with the context.
    """

    # Create a SQLAlchemy engine from the configuration
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,                # Don't pool connections for migrations
    )
    
    # Connect to the database
    with connectable.connect() as connection:
        # Configure the migration context with our connection and metadata
        context.configure(
            connection=connection,              # Use our established connection
            target_metadata=target_metadata,    # Our models' metadata
        )
        
        # Run the migrations within a transaction
        with context.begin_transaction():
            context.run_migrations()

# Determine which mode to run in (offline or online)
# This is Alembic's standard way of choosing the execution mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
