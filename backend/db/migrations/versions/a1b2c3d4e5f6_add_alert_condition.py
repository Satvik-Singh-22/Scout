"""add alert_condition to scheduled_queries

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-04-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('scheduled_queries', sa.Column('alert_condition', sa.Text(), nullable=True))
    op.add_column('scheduled_queries', sa.Column('alert_severity', sa.String(20), nullable=True, server_default='MEDIUM'))


def downgrade() -> None:
    op.drop_column('scheduled_queries', 'alert_severity')
    op.drop_column('scheduled_queries', 'alert_condition')
