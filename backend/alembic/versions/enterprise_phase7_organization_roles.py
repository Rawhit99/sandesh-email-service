"""Per-user organization_role (admin | member).

Revision ID: enterprise_phase7
Revises: enterprise_phase6
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "enterprise_phase7"
down_revision = "enterprise_phase6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "organization_role" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "organization_role", sa.String(length=20), nullable=True
            ),
        )

    conn = bind
    conn.execute(
        text(
            """
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY organization_id
                           ORDER BY id
                       ) AS rn
                FROM users
                WHERE organization_id IS NOT NULL
                  AND (
                      organization_role IS NULL
                      OR TRIM(organization_role) = ''
                  )
            )
            UPDATE users u
            SET organization_role = CASE
                WHEN ranked.rn = 1 THEN 'admin'
                ELSE 'member'
            END
            FROM ranked
            WHERE u.id = ranked.id
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "organization_role" in cols:
        op.drop_column("users", "organization_role")
