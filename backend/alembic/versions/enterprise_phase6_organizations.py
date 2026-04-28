"""Organizations table and users.organization_id.

Revision ID: enterprise_phase6
Revises: enterprise_phase5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "enterprise_phase6"
down_revision = "enterprise_phase5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return

    if not insp.has_table("organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_organizations_id"), "organizations", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_organizations_name"),
            "organizations",
            ["name"],
            unique=True,
        )
    else:
        org_indexes = {ix["name"] for ix in insp.get_indexes("organizations")}
        if "ix_organizations_name" not in org_indexes:
            op.create_index(
                op.f("ix_organizations_name"),
                "organizations",
                ["name"],
                unique=True,
            )

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "organization_id" not in user_cols:
        op.add_column(
            "users",
            sa.Column("organization_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            op.f("fk_users_organization_id_organizations"),
            "users",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            op.f("ix_users_organization_id"),
            "users",
            ["organization_id"],
            unique=False,
        )

    # Backfill org rows from legacy organization_name and link users.
    conn = bind
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT TRIM(organization_name) AS n
            FROM users
            WHERE organization_name IS NOT NULL
              AND TRIM(organization_name) <> ''
            """
        )
    ).fetchall()
    for (raw_name,) in rows:
        if not raw_name:
            continue
        name = str(raw_name).strip()
        if not name:
            continue
        existing = conn.execute(
            text("SELECT id FROM organizations WHERE name = :name"),
            {"name": name},
        ).fetchone()
        if not existing:
            conn.execute(
                text(
                    """
                    INSERT INTO organizations (name, created_at, updated_at)
                    VALUES (:name, NOW(), NOW())
                    """
                ),
                {"name": name},
            )
        row = conn.execute(
            text("SELECT id FROM organizations WHERE name = :name"),
            {"name": name},
        ).fetchone()
        if row:
            oid = row[0]
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET organization_id = :oid
                    WHERE TRIM(organization_name) = :name
                      AND (organization_id IS NULL OR organization_id <> :oid)
                    """
                ),
                {"oid": oid, "name": name},
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("users"):
        return
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "organization_id" in user_cols:
        op.drop_index(op.f("ix_users_organization_id"), table_name="users")
        op.drop_constraint(
            op.f("fk_users_organization_id_organizations"),
            "users",
            type_="foreignkey",
        )
        op.drop_column("users", "organization_id")
    if insp.has_table("organizations"):
        op.drop_index(
            op.f("ix_organizations_name"), table_name="organizations"
        )
        op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
        op.drop_table("organizations")
