"""add vocal to trainingtype enum

Revision ID: c0786e033877
Revises: 2abf5ebdd660
Create Date: 2025-11-06 09:53:23.304187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0786e033877'
down_revision: Union[str, Sequence[str], None] = '2abf5ebdd660'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # trainingtype enum에 'vocal' 값을 추가 (코드에서 소문자 "vocal" 사용)
    # 참고: DB enum은 WORD, SENTENCE (대문자)이지만, 코드에서는 소문자 value 사용
    # PostgreSQL은 ENUM 값 삭제가 불가능하므로, 기존 값은 유지하고 새 값만 추가
    # 이미 'vocal'이 추가되어 있다면 에러가 발생하므로, DO 블록으로 안전하게 처리
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'vocal' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'trainingtype')
            ) THEN
                ALTER TYPE trainingtype ADD VALUE 'vocal';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL ENUM 타입에서 값을 삭제할 수 없으므로 downgrade는 비워둡니다
    # 기존 데이터 중 'vocal' 값을 사용하는 레코드가 있다면 수동으로 처리해야 합니다
    pass

