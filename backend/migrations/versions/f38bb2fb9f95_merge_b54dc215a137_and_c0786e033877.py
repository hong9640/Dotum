"""merge b54dc215a137 and c0786e033877

Revision ID: f38bb2fb9f95
Revises: b54dc215a137, c0786e033877
Create Date: 2025-11-06 10:36:45.640824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'f38bb2fb9f95'
down_revision: Union[str, Sequence[str], None] = ('b54dc215a137', 'c0786e033877')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
