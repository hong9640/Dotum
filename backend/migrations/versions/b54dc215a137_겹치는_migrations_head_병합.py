"""겹치는 migrations head 병합

Revision ID: b54dc215a137
Revises: 2abf5ebdd660, 4eb002a9512c
Create Date: 2025-11-06 10:00:20.145838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'b54dc215a137'
down_revision: Union[str, Sequence[str], None] = ('2abf5ebdd660', '4eb002a9512c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
