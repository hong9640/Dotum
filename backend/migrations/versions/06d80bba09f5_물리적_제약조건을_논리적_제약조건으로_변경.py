"""물리적 제약조건을 논리적 제약조건으로 변경

Revision ID: 06d80bba09f5
Revises: 40976aba46d9
Create Date: 2025-10-23 14:40:43.882350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '06d80bba09f5'
down_revision: Union[str, Sequence[str], None] = '40976aba46d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
