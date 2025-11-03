"""

Revision ID: 11e49b87a854
Revises: 653c2972f69b
Create Date: 2025-10-23 16:21:01.328597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '11e49b87a854'
down_revision: Union[str, Sequence[str], None] = '653c2972f69b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
