"""Email template default attachments JSON.

Revision ID: enterprise_phase2
Revises: enterprise_phase1
Create Date: 2026-04-12

Idempotent: skips if column already exists.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

revision = "enterprise_phase2"
down_revision = "enterprise_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("email_templates"):
        return
    cols = {c["name"] for c in insp.get_columns("email_templates")}
    if "default_attachments" not in cols:
        try:
            op.add_column(
                "email_templates",
                sa.Column("default_attachments", JSONB, nullable=True),
            )
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("email_templates"):
        return
    cols = {c["name"] for c in insp.get_columns("email_templates")}
    if "default_attachments" in cols:
        try:
            op.drop_column("email_templates", "default_attachments")
        except Exception:
            pass
