"""init

Revision ID: b249ba5637cf
Revises: 
Create Date: 2025-11-14 11:37:07.223861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'b249ba5637cf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 테이블 존재 여부 확인
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 1. train_item_praat_feedback 테이블 처리
    item_table_name = None
    if 'train_item_praat_feedback' in tables:
        item_table_name = 'train_item_praat_feedback'
    elif 'training_item_praat_feedback' in tables:
        item_table_name = 'training_item_praat_feedback'
    
    if not item_table_name:
        # train_item_praat_feedback 테이블 생성
        op.create_table('train_item_praat_feedback',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('praat_features_id', sa.Integer(), nullable=False),
            sa.Column('ai_model_id', sa.Integer(), nullable=True),
            sa.Column('item_feedback', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_train_item_praat_feedback_praat_features_id'), 'train_item_praat_feedback', ['praat_features_id'], unique=False)
        op.create_index(op.f('ix_train_item_praat_feedback_ai_model_id'), 'train_item_praat_feedback', ['ai_model_id'], unique=False)
    
    # 2. train_session_praat_feedback 테이블 처리
    session_table_name = None
    if 'train_session_praat_feedback' in tables:
        session_table_name = 'train_session_praat_feedback'
    elif 'training_session_praat_feedback' in tables:
        session_table_name = 'training_session_praat_feedback'
    
    if session_table_name:
        # 테이블이 존재하는 경우에만 컬럼 추가/삭제
        columns = [col['name'] for col in inspector.get_columns(session_table_name)]
        
        # ai_model_id 컬럼이 없으면 추가
        if 'ai_model_id' not in columns:
            op.add_column(session_table_name, sa.Column('ai_model_id', sa.Integer(), nullable=True))
            # 기존 데이터에 대한 기본값 설정 (필요시)
            op.execute(f"UPDATE {session_table_name} SET ai_model_id = 1 WHERE ai_model_id IS NULL")
            op.alter_column(session_table_name, 'ai_model_id', nullable=False)
        
        # 인덱스 생성 (없는 경우만)
        indexes = [idx['name'] for idx in inspector.get_indexes(session_table_name)]
        if 'ix_train_session_praat_feedback_ai_model_id' not in indexes and 'ix_training_session_praat_feedback_ai_model_id' not in indexes:
            op.create_index(op.f('ix_train_session_praat_feedback_ai_model_id'), session_table_name, ['ai_model_id'], unique=False)
        
        # model_version 컬럼이 있으면 삭제
        if 'model_version' in columns:
            op.drop_column(session_table_name, 'model_version')
    else:
        # 테이블이 존재하지 않으면 생성 (초기 마이그레이션인 경우)
        # train_session_praat_feedback 테이블 생성 (나중에 training_으로 이름 변경됨)
        op.create_table('train_session_praat_feedback',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_praat_result_id', sa.Integer(), nullable=False),
            sa.Column('ai_model_id', sa.Integer(), nullable=False),
            sa.Column('feedback_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_train_session_praat_feedback_session_praat_result_id'), 'train_session_praat_feedback', ['session_praat_result_id'], unique=False)
        op.create_index(op.f('ix_train_session_praat_feedback_ai_model_id'), 'train_session_praat_feedback', ['ai_model_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 테이블 존재 여부 확인
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # train_session_praat_feedback 또는 training_session_praat_feedback 테이블 확인
    table_name = None
    if 'train_session_praat_feedback' in tables:
        table_name = 'train_session_praat_feedback'
    elif 'training_session_praat_feedback' in tables:
        table_name = 'training_session_praat_feedback'
    
    if table_name:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
        
        # ai_model_id 컬럼이 있으면 삭제
        if 'ai_model_id' in columns:
            # 인덱스 먼저 삭제
            if 'ix_train_session_praat_feedback_ai_model_id' in indexes:
                op.drop_index(op.f('ix_train_session_praat_feedback_ai_model_id'), table_name=table_name)
            elif 'ix_training_session_praat_feedback_ai_model_id' in indexes:
                op.drop_index('ix_training_session_praat_feedback_ai_model_id', table_name=table_name)
            op.drop_column(table_name, 'ai_model_id')
        
        # model_version 컬럼이 없으면 추가
        if 'model_version' not in columns:
            op.add_column(table_name, sa.Column('model_version', sa.VARCHAR(), autoincrement=False, nullable=False))
