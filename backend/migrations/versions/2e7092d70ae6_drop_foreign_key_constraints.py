"""Drop foreign key constraints

Revision ID: 2e7092d70ae6
Revises: 06d80bba09f5
Create Date: 2025-10-23 14:44:27.126375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '2e7092d70ae6'
down_revision: Union[str, Sequence[str], None] = '06d80bba09f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # FK 제약조건 제거 (논리적 관계만 유지, 물리적 제약조건 제거)
    op.drop_constraint('train_results_train_sentences_id_fkey', 'train_results', type_='foreignkey')
    op.drop_constraint('train_sentences_train_words_id_fkey', 'train_sentences', type_='foreignkey')


def downgrade() -> None:
    """Downgrade schema."""
    # FK 제약조건 복구 (롤백 시)
    op.create_foreign_key(
        'train_sentences_train_words_id_fkey', 
        'train_sentences', 'train_words', 
        ['train_words_id'], ['id']
    )
    op.create_foreign_key(
        'train_results_train_sentences_id_fkey', 
        'train_results', 'train_sentences', 
        ['train_sentences_id'], ['id']
    )
