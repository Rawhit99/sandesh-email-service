"""User-scoped integration + email delivery JSON (DB-backed).

Revision ID: enterprise_phase5
Revises: enterprise_phase4
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

revision = "enterprise_phase5"
down_revision = "enterprise_phase4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "integration_settings" not in cols:
        op.add_column(
            "users", sa.Column("integration_settings", JSONB(), nullable=True)
        )
    if "email_delivery_settings" not in cols:
        op.add_column(
            "users",
            sa.Column("email_delivery_settings", JSONB(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "email_delivery_settings" in cols:
        op.drop_column("users", "email_delivery_settings")
    if "integration_settings" in cols:
        op.drop_column("users", "integration_settings")
