"""

Revision ID: c46299d689b9
Revises: 11e49b87a854
Create Date: 2025-10-23 16:24:29.929503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'c46299d689b9'
down_revision: Union[str, Sequence[str], None] = '11e49b87a854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
