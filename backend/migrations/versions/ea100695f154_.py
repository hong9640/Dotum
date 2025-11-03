"""

Revision ID: ea100695f154
Revises: 657b542e424c
Create Date: 2025-10-23 15:14:14.874658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'ea100695f154'
down_revision: Union[str, Sequence[str], None] = '657b542e424c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
