"""훈련 결과 table 단어 훈련 결과, 문장 훈련 결과 table로 분리

Revision ID: 75b5ff0957e8
Revises: 3d5ed6e2b25d
Create Date: 2025-10-23 20:19:25.362292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '75b5ff0957e8'
down_revision: Union[str, Sequence[str], None] = '3d5ed6e2b25d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
