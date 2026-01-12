import os, sys

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, BASE_DIR)

from logging.config import fileConfig
import pkgutil, importlib
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.common.base.base_model import Base
from pathlib import Path
import app.modules as modules_root


def discover_module_migration_paths() -> list[str]:
    """
    Find all module migration version directories.
    Example:
      app/modules/iam/migrations/versions
    """
    paths = []

    modules_base = Path(modules_root.__file__).parent

    for module_dir in modules_base.iterdir():
        if not module_dir.is_dir():
            continue

        migrations_dir = module_dir / "migrations" / "versions"
        if migrations_dir.exists():
            paths.append(str(migrations_dir.resolve()))

    return paths


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# -------------------------------------------
# Register ALL migration locations
# -------------------------------------------

base_versions = Path(__file__).parent / "versions"
module_versions = discover_module_migration_paths()

all_version_locations = [str(base_versions.resolve()), *module_versions]

config.set_main_option(
    "version_locations",
    " ".join(all_version_locations)
)


# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import model
# target_metadata = model.Base.metadata
# target_metadata = None


def import_submodules(package):
    package_path = package.__path__
    prefix = package.__name__ + "."

    for _, module_name, is_pkg in pkgutil.walk_packages(package_path, prefix):
        module = importlib.import_module(module_name)

import_submodules(modules_root)

# from app.models import SQLModel  # noqa
from config.config import settings # noqa

# target_metadata = SQLModel.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_sync_url():
    """
    Alembic MUST use a synchronous database URL.
    """
    return settings.SYNC_DATABASE_URL



def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_sync_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    sync_url = get_sync_url()
    
    
    configuration = config.get_section(config.config_ini_section)
    # configuration["sqlalchemy.url"] = get_url()
    configuration["sqlalchemy.url"] = sync_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
