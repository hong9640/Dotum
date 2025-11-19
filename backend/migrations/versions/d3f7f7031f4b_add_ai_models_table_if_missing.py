"""ensure ai_models table exists

Revision ID: d3f7f7031f4b
Revises: 7d73f6e3f1f8
Create Date: 2025-11-19 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f7f7031f4b'
down_revision: Union[str, Sequence[str], None] = '7d73f6e3f1f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ai_models table if it is missing."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'ai_models' not in inspector.get_table_names():
        op.create_table(
            'ai_models',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('version', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    """Drop ai_models table (created by this revision)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'ai_models' in inspector.get_table_names():
        op.drop_table('ai_models')

