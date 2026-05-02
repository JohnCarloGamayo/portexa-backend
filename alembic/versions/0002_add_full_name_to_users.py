"""add full_name to users

Revision ID: 0002_add_full_name_to_users
Revises: 0001_create_users
Create Date: 2026-05-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_full_name_to_users"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "full_name")