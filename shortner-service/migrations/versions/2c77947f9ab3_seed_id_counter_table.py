"""seed id counter table

Revision ID: 2c77947f9ab3
Revises: 04f4218549fe
Create Date: 2025-08-14 20:20:20.631337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from app.config import settings

# revision identifiers, used by Alembic.
revision: str = '2c77947f9ab3'
down_revision: Union[str, Sequence[str], None] = '04f4218549fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        f"""
            INSERT INTO idcounter (key, next_id)
            SELECT '{settings.id_counter_key}', 1
            WHERE NOT EXISTS (
              SELECT 1
              FROM idcounter
              WHERE key = '{settings.id_counter_key}'
            );
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        f"""
            DELETE FROM idcounter WHERE key = '{settings.id_counter_key}';
        """
    )
