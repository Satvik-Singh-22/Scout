# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""add agent_mode to chatrooms

Revision ID: b2c3d4e5f607
Revises: 8c2cd5d95285
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f607'
down_revision = '8c2cd5d95285'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'chatrooms',
        sa.Column('agent_mode', sa.String(20), nullable=False, server_default='DATABASE'),
    )
    op.create_check_constraint(
        'ck_chatrooms_agent_mode',
        'chatrooms',
        "agent_mode IN ('DATABASE', 'SLACK_JIRA')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_chatrooms_agent_mode', 'chatrooms', type_='check')
    op.drop_column('chatrooms', 'agent_mode')
