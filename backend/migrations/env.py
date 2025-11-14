from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from sqlmodel import SQLModel

# Import settings to get DB_URL
from api.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get DB_URL from settings and convert for Alembic compatibility
# asyncpg (used by FastAPI) → psycopg2 (used by Alembic)
db_url = settings.DB_URL
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

# add your model's MetaData object here
# for 'autogenerate' support
# Import all models here to ensure they are registered with SQLModel
from api.src.train.models import (
    TrainWords, 
    TrainSentences, 
    TrainingSession,
    TrainingType,
    TrainingSessionStatus,
    TrainingItem,
    PraatFeatures
)
from api.src.train.models.session_praat_result import SessionPraatResult
from api.src.train.models.ai_model import AIModel
from api.src.train.models.training_session_praat_feedback import TrainSessionPraatFeedback
from api.src.train.models.training_item_praat_feedback import TrainItemPraatFeedback
from api.src.user.user_model import User
from api.src.token.token_model import RefreshToken

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use db_url from settings (already converted above)
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use db_url from settings (already converted above)
    connectable = engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
