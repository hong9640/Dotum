"""modified training_item_praat_feedback table

Revision ID: fbc2d3cfc97b
Revises: b249ba5637cf
Create Date: 2025-11-14 12:27:15.140372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'fbc2d3cfc97b'
down_revision: Union[str, Sequence[str], None] = 'b249ba5637cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 테이블 존재 여부 확인
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # train_item_praat_feedback 또는 training_item_praat_feedback 테이블 확인
    table_name = None
    if 'train_item_praat_feedback' in tables:
        table_name = 'train_item_praat_feedback'
    elif 'training_item_praat_feedback' in tables:
        table_name = 'training_item_praat_feedback'
    
    if table_name:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # item_feedback 컬럼이 없으면 추가
        if 'item_feedback' not in columns:
            op.add_column(table_name, sa.Column('item_feedback', sa.Text(), nullable=True))
        
        # 삭제할 컬럼들이 있으면 삭제
        if 'voice_health_feedback' in columns:
            op.drop_column(table_name, 'voice_health_feedback')
        if 'vowel_distortion_feedback' in columns:
            op.drop_column(table_name, 'vowel_distortion_feedback')
        if 'overall_feedback' in columns:
            op.drop_column(table_name, 'overall_feedback')
        if 'sound_stability_feedback' in columns:
            op.drop_column(table_name, 'sound_stability_feedback')
        if 'voice_clarity_feedback' in columns:
            op.drop_column(table_name, 'voice_clarity_feedback')


def downgrade() -> None:
    """Downgrade schema."""
    # 테이블 존재 여부 확인
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # train_item_praat_feedback 또는 training_item_praat_feedback 테이블 확인
    table_name = None
    if 'train_item_praat_feedback' in tables:
        table_name = 'train_item_praat_feedback'
    elif 'training_item_praat_feedback' in tables:
        table_name = 'training_item_praat_feedback'
    
    if table_name:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # 추가할 컬럼들이 없으면 추가
        if 'voice_clarity_feedback' not in columns:
            op.add_column(table_name, sa.Column('voice_clarity_feedback', sa.TEXT(), autoincrement=False, nullable=True))
        if 'sound_stability_feedback' not in columns:
            op.add_column(table_name, sa.Column('sound_stability_feedback', sa.TEXT(), autoincrement=False, nullable=True))
        if 'overall_feedback' not in columns:
            op.add_column(table_name, sa.Column('overall_feedback', sa.TEXT(), autoincrement=False, nullable=True))
        if 'vowel_distortion_feedback' not in columns:
            op.add_column(table_name, sa.Column('vowel_distortion_feedback', sa.TEXT(), autoincrement=False, nullable=True))
        if 'voice_health_feedback' not in columns:
            op.add_column(table_name, sa.Column('voice_health_feedback', sa.TEXT(), autoincrement=False, nullable=True))
        
        # item_feedback 컬럼이 있으면 삭제
        if 'item_feedback' in columns:
            op.drop_column(table_name, 'item_feedback')
