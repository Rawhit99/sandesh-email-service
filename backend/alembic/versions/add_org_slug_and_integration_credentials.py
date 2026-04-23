"""add org_slug and integration_credentials table

Revision ID: add_org_slug_creds
Revises: enterprise_phase8
Create Date: 2026-04-13 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

revision = 'add_org_slug_creds'
down_revision = 'enterprise_phase8'
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    insp = Inspector.from_engine(conn)
    return column in {c["name"] for c in insp.get_columns(table)}


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


def upgrade():
    conn = op.get_bind()

    # ── organizations.org_slug ──────────────────────────────────────────────
    if not _column_exists(conn, 'organizations', 'org_slug'):
        op.add_column('organizations', sa.Column('org_slug', sa.String(60), nullable=True))

    if not _constraint_exists(conn, 'organizations', 'uq_organizations_org_slug'):
        op.create_unique_constraint('uq_organizations_org_slug', 'organizations', ['org_slug'])

    if not _index_exists(conn, 'organizations', 'ix_organizations_org_slug'):
        op.create_index('ix_organizations_org_slug', 'organizations', ['org_slug'], unique=True)

    # ── integration_credentials table ──────────────────────────────────────
    if not _table_exists(conn, 'integration_credentials'):
        op.create_table(
            'integration_credentials',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('channel', sa.String(60), nullable=False),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if not _index_exists(conn, 'integration_credentials', 'ix_intcred_id'):
        op.create_index('ix_intcred_id', 'integration_credentials', ['id'])

    if not _index_exists(conn, 'integration_credentials', 'ix_intcred_user_channel'):
        op.create_index('ix_intcred_user_channel', 'integration_credentials', ['user_id', 'channel'])

    if not _constraint_exists(conn, 'integration_credentials', 'uq_intcred_user_channel_name'):
        op.create_unique_constraint(
            'uq_intcred_user_channel_name',
            'integration_credentials',
            ['user_id', 'channel', 'name'],
        )


def downgrade():
    conn = op.get_bind()

    if _constraint_exists(conn, 'integration_credentials', 'uq_intcred_user_channel_name'):
        op.drop_constraint('uq_intcred_user_channel_name', 'integration_credentials', type_='unique')

    if _index_exists(conn, 'integration_credentials', 'ix_intcred_user_channel'):
        op.drop_index('ix_intcred_user_channel', table_name='integration_credentials')

    if _index_exists(conn, 'integration_credentials', 'ix_intcred_id'):
        op.drop_index('ix_intcred_id', table_name='integration_credentials')

    if _table_exists(conn, 'integration_credentials'):
        op.drop_table('integration_credentials')

    if _index_exists(conn, 'organizations', 'ix_organizations_org_slug'):
        op.drop_index('ix_organizations_org_slug', table_name='organizations')

    if _constraint_exists(conn, 'organizations', 'uq_organizations_org_slug'):
        op.drop_constraint('uq_organizations_org_slug', 'organizations', type_='unique')

    if _column_exists(conn, 'organizations', 'org_slug'):
        op.drop_column('organizations', 'org_slug')

