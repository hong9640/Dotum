"""first alembic

Revision ID: abc1cec616ad
Revises: e85290b3822a
Create Date: 2025-10-21 10:31:54.528741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'abc1cec616ad'
down_revision: Union[str, Sequence[str], None] = 'e85290b3822a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
