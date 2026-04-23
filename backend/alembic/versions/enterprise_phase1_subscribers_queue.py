"""Subscribers, execution grouping, delivery metadata, seen flag.

Revision ID: enterprise_phase1
Revises: add_auth_tables
Create Date: 2026-04-12

Idempotent: safe when tables/columns already exist.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "enterprise_phase1"
down_revision = "add_auth_tables"
branch_labels = None
depends_on = None


def _notif_columns(bind) -> set:
    insp = inspect(bind)
    if not insp.has_table("notifications"):
        return set()
    return {c["name"] for c in insp.get_columns("notifications")}


def _notif_indexes(bind) -> set:
    insp = inspect(bind)
    if not insp.has_table("notifications"):
        return set()
    return {ix["name"] for ix in insp.get_indexes("notifications")}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("subscribers"):
        op.create_table(
            "subscribers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("subscriber_id", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("data", sa.JSON(), nullable=True),
            sa.Column("channels", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "subscriber_id", name="uq_subscriber_user_ext"),
        )
        try:
            op.create_index(op.f("ix_subscribers_subscriber_id"), "subscribers", ["subscriber_id"], unique=False)
        except Exception:
            pass
        try:
            op.create_index(op.f("ix_subscribers_user_id"), "subscribers", ["user_id"], unique=False)
        except Exception:
            pass
    else:
        idx = {ix["name"] for ix in insp.get_indexes("subscribers")}
        if "ix_subscribers_subscriber_id" not in idx:
            try:
                op.create_index(op.f("ix_subscribers_subscriber_id"), "subscribers", ["subscriber_id"], unique=False)
            except Exception:
                pass
        if "ix_subscribers_user_id" not in idx:
            try:
                op.create_index(op.f("ix_subscribers_user_id"), "subscribers", ["user_id"], unique=False)
            except Exception:
                pass

    if not insp.has_table("notifications"):
        return

    cols = _notif_columns(bind)
    def _addcol(name: str, col) -> None:
        if name in cols:
            return
        try:
            op.add_column("notifications", col)
        except Exception:
            pass

    _addcol("subscriber_external_id", sa.Column("subscriber_external_id", sa.String(length=255), nullable=True))
    _addcol("execution_run_id", sa.Column("execution_run_id", sa.String(length=36), nullable=True))
    _addcol("channels_requested", sa.Column("channels_requested", sa.JSON(), nullable=True))
    _addcol("from_email_override", sa.Column("from_email_override", sa.String(length=255), nullable=True))
    _addcol("sender_display_name", sa.Column("sender_display_name", sa.String(length=255), nullable=True))
    _addcol("attachments", sa.Column("attachments", sa.JSON(), nullable=True))
    _addcol("seen_at", sa.Column("seen_at", sa.DateTime(), nullable=True))

    idxn = _notif_indexes(bind)
    if "ix_notifications_execution_run_id" not in idxn:
        try:
            op.create_index("ix_notifications_execution_run_id", "notifications", ["execution_run_id"])
        except Exception:
            pass
    if "ix_notifications_subscriber_external_id" not in idxn:
        try:
            op.create_index(
                "ix_notifications_subscriber_external_id",
                "notifications",
                ["subscriber_external_id"],
            )
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("notifications"):
        for ix in ("ix_notifications_subscriber_external_id", "ix_notifications_execution_run_id"):
            try:
                op.drop_index(ix, table_name="notifications")
            except Exception:
                pass
        cols = {c["name"] for c in insp.get_columns("notifications")}
        for col in (
            "seen_at",
            "attachments",
            "sender_display_name",
            "from_email_override",
            "channels_requested",
            "execution_run_id",
            "subscriber_external_id",
        ):
            if col in cols:
                try:
                    op.drop_column("notifications", col)
                except Exception:
                    pass
    if insp.has_table("subscribers"):
        try:
            op.drop_index(op.f("ix_subscribers_user_id"), table_name="subscribers")
        except Exception:
            pass
        try:
            op.drop_index(op.f("ix_subscribers_subscriber_id"), table_name="subscribers")
        except Exception:
            pass
        op.drop_table("subscribers")
