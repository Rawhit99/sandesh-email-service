"""Platform admin flag + organization.service_user_id (tenant account per org).

Revision ID: enterprise_phase8
Revises: enterprise_phase7
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "enterprise_phase8"
down_revision = "enterprise_phase7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "is_platform_admin" not in user_cols:
        op.add_column(
            "users",
            sa.Column(
                "is_platform_admin",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
        )
        op.alter_column("users", "is_platform_admin", server_default=None)

    if insp.has_table("organizations"):
        org_cols = {c["name"] for c in insp.get_columns("organizations")}
        if "service_user_id" not in org_cols:
            op.add_column(
                "organizations",
                sa.Column("service_user_id", sa.Integer(), nullable=True),
            )
            op.create_index(
                op.f("ix_organizations_service_user_id"),
                "organizations",
                ["service_user_id"],
                unique=True,
            )
            op.create_foreign_key(
                op.f("fk_organizations_service_user_id_users"),
                "organizations",
                "users",
                ["service_user_id"],
                ["id"],
                ondelete="SET NULL",
            )

        conn = bind
        conn.execute(
            text(
                """
                UPDATE organizations o
                SET service_user_id = sub.uid
                FROM (
                    SELECT organization_id AS oid, MIN(id) AS uid
                    FROM users
                    WHERE organization_id IS NOT NULL
                    GROUP BY organization_id
                ) sub
                WHERE o.id = sub.oid
                  AND (
                      o.service_user_id IS NULL
                      OR o.service_user_id <> sub.uid
                  )
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("organizations"):
        org_cols = {c["name"] for c in insp.get_columns("organizations")}
        if "service_user_id" in org_cols:
            op.drop_constraint(
                op.f("fk_organizations_service_user_id_users"),
                "organizations",
                type_="foreignkey",
            )
            op.drop_index(
                op.f("ix_organizations_service_user_id"),
                table_name="organizations",
            )
            op.drop_column("organizations", "service_user_id")
    if insp.has_table("users"):
        user_cols = {c["name"] for c in insp.get_columns("users")}
        if "is_platform_admin" in user_cols:
            op.drop_column("users", "is_platform_admin")
