"""add cascade delete to embedding chunks

Revision ID: 973165ac1f8d
Revises: 2aaad85e53a2
Create Date: 2026-05-26 00:30:19.960795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '973165ac1f8d'
down_revision: Union[str, Sequence[str], None] = '2aaad85e53a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
        op.drop_constraint(
        op.f('embedding_chunks_note_id_fkey'),
        'embedding_chunks',
        type_='foreignkey'
    )

        op.create_foreign_key(
        None,
        'embedding_chunks',
        'notes',
        ['note_id'],
        ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    """Downgrade schema."""
  
    op.drop_constraint(
        None,
        'embedding_chunks',
        type_='foreignkey'
    )

    op.create_foreign_key(
        op.f('embedding_chunks_note_id_fkey'),
        'embedding_chunks',
        'notes',
        ['note_id'],
        ['id']
    )