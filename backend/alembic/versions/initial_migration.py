"""Initial migration

Revision ID: initial_migration
Revises:
Create Date: 2024-xx-xx

Idempotent: skips if email_templates already exists (e.g. created by SQLAlchemy create_all).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

revision = "initial_migration"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("email_templates"):
        return

    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("variables", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id"),
    )
    op.create_index(op.f("ix_email_templates_template_id"), "email_templates", ["template_id"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("email_templates"):
        return
    op.drop_index(op.f("ix_email_templates_template_id"), table_name="email_templates")
    op.drop_table("email_templates")
