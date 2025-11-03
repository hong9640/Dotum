"""물리적 제약조건을 논리적 제약조건으로 변경

Revision ID: 657b542e424c
Revises: 2e7092d70ae6
Create Date: 2025-10-23 14:56:44.070373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '657b542e424c'
down_revision: Union[str, Sequence[str], None] = '2e7092d70ae6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
