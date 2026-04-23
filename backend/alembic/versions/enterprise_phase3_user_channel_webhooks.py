"""Per-user channel webhooks and notification.user_id.

Revision ID: enterprise_phase3
Revises: enterprise_phase2
Create Date: 2026-04-12

Idempotent: skips columns/indexes that already exist.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

revision = "enterprise_phase3"
down_revision = "enterprise_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if insp.has_table("users"):
        cols = {c["name"] for c in insp.get_columns("users")}
        if "channel_webhooks" not in cols:
            op.add_column(
                "users",
                sa.Column(
                    "channel_webhooks",
                    JSONB(),
                    nullable=True,
                    server_default=sa.text("'{}'::jsonb"),
                ),
            )

    if insp.has_table("notifications"):
        ncols = {c["name"] for c in insp.get_columns("notifications")}
        if "user_id" not in ncols:
            op.add_column(
                "notifications",
                sa.Column("user_id", sa.Integer(), nullable=True),
            )
            op.create_foreign_key(
                "fk_notifications_user_id_users",
                "notifications",
                "users",
                ["user_id"],
                ["id"],
                ondelete="SET NULL",
            )
            op.create_index(
                "ix_notifications_user_id", "notifications", ["user_id"]
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("notifications"):
        ncols = {c["name"] for c in insp.get_columns("notifications")}
        if "user_id" in ncols:
            op.drop_index(
                "ix_notifications_user_id",
                table_name="notifications",
                if_exists=True,
            )
            op.drop_constraint(
                "fk_notifications_user_id_users",
                "notifications",
                type_="foreignkey",
            )
            op.drop_column("notifications", "user_id")
    if insp.has_table("users"):
        cols = {c["name"] for c in insp.get_columns("users")}
        if "channel_webhooks" in cols:
            op.drop_column("users", "channel_webhooks")
