"""add indexes for training session date queries

Revision ID: 7d73f6e3f1f8
Revises: edf9cb7ecf83
Create Date: 2025-11-19 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7d73f6e3f1f8'
down_revision: Union[str, Sequence[str], None] = 'a8327b7e6f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create supporting indexes for date-based queries."""
    op.create_index(
        'ix_training_sessions_training_date',
        'training_sessions',
        ['training_date'],
        unique=False,
    )
    op.create_index(
        'ix_training_sessions_user_id_training_date',
        'training_sessions',
        ['user_id', 'training_date'],
        unique=False,
    )


def downgrade() -> None:
    """Drop indexes for date-based queries."""
    op.drop_index('ix_training_sessions_user_id_training_date', table_name='training_sessions')
    op.drop_index('ix_training_sessions_training_date', table_name='training_sessions')

