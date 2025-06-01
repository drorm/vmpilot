"""initial schema

Revision ID: 57dc007f6d46
Revises: 
Create Date: 2025-05-10 18:47:49.327447

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "57dc007f6d46"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        initial_request TEXT,
        project_root TEXT,
        messages TEXT NOT NULL,
        cache_info TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )
    op.execute(
        """
    CREATE TABLE IF NOT EXISTS exchanges (
        exchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT NOT NULL,
        model TEXT NOT NULL,
        request TEXT,
        cost JSON,
        start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS exchanges;")
    op.execute("DROP TABLE IF EXISTS chats;")
