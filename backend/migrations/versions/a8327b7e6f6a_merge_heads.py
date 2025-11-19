"""merge heads c064937e2ae0 and edf9cb7ecf83

Revision ID: a8327b7e6f6a
Revises: ('edf9cb7ecf83', 'c064937e2ae0')
Create Date: 2025-11-19 16:08:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'a8327b7e6f6a'
down_revision: Union[str, Sequence[str], None] = ('edf9cb7ecf83', 'c064937e2ae0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op merge migration."""
    pass


def downgrade() -> None:
    """Recreate divergent heads if necessary."""
    pass

