"""add org_template_settings table

Revision ID: org_template_settings
Revises: add_org_slug_creds
Create Date: 2026-04-13 16:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


def _table_exists(conn, table: str) -> bool:
    insp = Inspector.from_engine(conn)
    return table in insp.get_table_names()


def _index_exists(conn, table: str, index: str) -> bool:
    insp = Inspector.from_engine(conn)
    return index in {i["name"] for i in insp.get_indexes(table)}


def _constraint_exists(conn, table: str, constraint: str) -> bool:
    insp = Inspector.from_engine(conn)
    ucs = insp.get_unique_constraints(table)
    return constraint in {c["name"] for c in ucs}


revision = "org_template_settings"
down_revision = "add_org_slug_creds"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    if not _table_exists(conn, "org_template_settings"):
        op.create_table(
            "org_template_settings",
            sa.Column(
                "id", sa.Integer(), primary_key=True, autoincrement=True
            ),
            sa.Column(
                "organization_id",
                sa.Integer(),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("template_id", sa.String(255), nullable=False),
            sa.Column(
                "is_enabled",
                sa.Boolean(),
                nullable=False,
                server_default="true",
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if _table_exists(conn, "org_template_settings"):
        if not _index_exists(
            conn, "org_template_settings", "ix_org_tpl_org_id"
        ):
            op.create_index(
                "ix_org_tpl_org_id",
                "org_template_settings",
                ["organization_id"],
            )

        if not _constraint_exists(
            conn, "org_template_settings", "uq_org_template_setting"
        ):
            op.create_unique_constraint(
                "uq_org_template_setting",
                "org_template_settings",
                ["organization_id", "template_id"],
            )


def downgrade():
    conn = op.get_bind()
    if _table_exists(conn, "org_template_settings"):
        op.drop_table("org_template_settings")
