"""Per-tenant email_templates.user_id and partial unique indexes.

Revision ID: enterprise_phase4
Revises: enterprise_phase3
Create Date: 2026-04-12

Replaces global unique(template_id) with:
- UNIQUE (template_id) WHERE user_id IS NULL  (legacy shared templates)
- UNIQUE (user_id, template_id) WHERE user_id IS NOT NULL
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "enterprise_phase4"
down_revision = "enterprise_phase3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("email_templates"):
        return

    for ix in insp.get_indexes("email_templates"):
        if ix.get("name") == "ix_email_templates_template_id" and ix.get(
            "unique"
        ):
            op.drop_index(
                "ix_email_templates_template_id", table_name="email_templates"
            )
            break

    cols = {c["name"] for c in insp.get_columns("email_templates")}
    if "user_id" not in cols:
        op.add_column(
            "email_templates",
            sa.Column("user_id", sa.Integer(), nullable=True),
        )

    insp = inspect(bind)
    fk_names = {
        fk.get("name") for fk in insp.get_foreign_keys("email_templates")
    }
    if "fk_email_templates_user_id_users" not in fk_names:
        op.create_foreign_key(
            "fk_email_templates_user_id_users",
            "email_templates",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    insp = inspect(bind)
    idx_names = {ix.get("name") for ix in insp.get_indexes("email_templates")}
    if "ix_email_templates_user_id" not in idx_names:
        op.create_index(
            "ix_email_templates_user_id", "email_templates", ["user_id"]
        )

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "uq_email_templates_legacy_template_id "
        "ON email_templates (template_id) WHERE user_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "uq_email_templates_user_template_id "
        "ON email_templates (user_id, template_id) WHERE user_id IS NOT NULL"
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("email_templates"):
        return

    op.execute("DROP INDEX IF EXISTS uq_email_templates_user_template_id")
    op.execute("DROP INDEX IF EXISTS uq_email_templates_legacy_template_id")

    cols = {c["name"] for c in insp.get_columns("email_templates")}
    if "user_id" in cols:
        op.execute("DROP INDEX IF EXISTS ix_email_templates_user_id")
        op.execute(
            "ALTER TABLE email_templates DROP CONSTRAINT IF EXISTS "
            "fk_email_templates_user_id_users"
        )
        op.drop_column("email_templates", "user_id")

    op.create_index(
        "ix_email_templates_template_id",
        "email_templates",
        ["template_id"],
        unique=True,
    )
