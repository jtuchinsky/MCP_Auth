"""Add tenant_name field to users table

Revision ID: 24d546efdc36
Revises: e340c902e215
Create Date: 2026-01-11 10:47:20.792459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24d546efdc36'
down_revision: Union[str, Sequence[str], None] = 'e340c902e215'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add tenant_name column to users table
    op.add_column('users', sa.Column('tenant_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove tenant_name column from users table
    op.drop_column('users', 'tenant_name')
